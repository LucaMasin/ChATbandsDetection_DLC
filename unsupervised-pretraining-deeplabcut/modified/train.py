'''
Adapted from DeeperCut by Eldar Insafutdinov
https://github.com/eldar/pose-tensorflow

'''
import logging, os
import threading
import argparse
from pathlib import Path
import tensorflow as tf
import tensorflow.contrib.slim as slim

from deeplabcut.pose_estimation_tensorflow.config import load_config
from deeplabcut.pose_estimation_tensorflow.dataset.factory import create as create_dataset
from deeplabcut.pose_estimation_tensorflow.nnet.net_factory import pose_net
from deeplabcut.pose_estimation_tensorflow.nnet.pose_net import get_batch_spec
from deeplabcut.pose_estimation_tensorflow.util.logging import setup_logging
from modified.validator import Validator
from modified import pose_net
from matplotlib import pyplot as plt
import numpy as np

def save_img_gray(img, name):
    img = plt.imshow(img, cmap='gray')
    plt.axis('off')
    img.axes.get_xaxis().set_visible(False)
    img.axes.get_yaxis().set_visible(False)
    plt.savefig(name, bbox_inches='tight', pad_inches=0)
    plt.close()

class LearningRate(object):
    def __init__(self, cfg):
        self.steps = cfg.multi_step
        self.current_step = 0

    def get_lr(self, iteration):
        lr = self.steps[self.current_step][0]
        if iteration == self.steps[self.current_step][1]:
            self.current_step += 1

        return lr

def setup_preloading(batch_spec):
    placeholders = {name: tf.placeholder(tf.float32, shape=spec) for (name, spec) in batch_spec.items()}
    names = placeholders.keys()
    placeholders_list = list(placeholders.values())

    QUEUE_SIZE = 20

    q = tf.FIFOQueue(QUEUE_SIZE, [tf.float32]*len(batch_spec))
    enqueue_op = q.enqueue(placeholders_list)
    batch_list = q.dequeue()

    batch = {}
    for idx, name in enumerate(names):
        batch[name] = batch_list[idx]
        batch[name].set_shape(batch_spec[name])
    return batch, enqueue_op, placeholders


def load_and_enqueue(sess, enqueue_op, coord, dataset, placeholders):
    while not coord.should_stop():
        batch_np = dataset.next_batch()
        food = {pl: batch_np[name] for (name, pl) in placeholders.items()}
        sess.run(enqueue_op, feed_dict=food)


def start_preloading(sess, enqueue_op, dataset, placeholders):
    coord = tf.train.Coordinator()

    t = threading.Thread(target=load_and_enqueue,
                         args=(sess, enqueue_op, coord, dataset, placeholders))
    t.start()

    return coord, t

def get_optimizer(loss_op, cfg):
    learning_rate = tf.placeholder(tf.float32, shape=[])

    if cfg.optimizer == "sgd":
        optimizer = tf.train.MomentumOptimizer(learning_rate=learning_rate, momentum=0.9)
    elif cfg.optimizer == "adam":
        optimizer = tf.train.AdamOptimizer(cfg.adam_lr)
    else:
        raise ValueError('unknown optimizer {}'.format(cfg.optimizer))
    train_op = slim.learning.create_train_op(loss_op, optimizer)

    return learning_rate, train_op


def train(cfg, pose_config_yaml,displayiters,saveiters,maxiters,max_to_keep=5):
    start_path=os.getcwd()
    os.chdir(str(Path(pose_config_yaml).parents[0])) #switch to folder of config_yaml (for logging)
    setup_logging()
    
    pose_cfg = load_config(pose_config_yaml)
    pose_cfg['batch_size']=1 #in case this was edited for analysis.

    # TODO:: Cleanup (Setting up validation)
    early_stopping_thresh = pose_cfg['early_stopping_threshold']
    validator = Validator(cfg, pose_cfg, pose_config_yaml)

    dataset = create_dataset(pose_cfg)
    batch_spec = get_batch_spec(pose_cfg)
    batch, enqueue_op, placeholders = setup_preloading(batch_spec)
    pose = pose_net.PoseNet(pose_cfg)
    losses = pose.train(batch)
    total_loss = losses['total_loss']

    for k, t in losses.items():
        tf.summary.scalar(k, t)
    merged_summaries = tf.summary.merge_all()

    variables_to_restore = slim.get_variables_to_restore(include=["resnet_v1"])
    restorer = tf.train.Saver(variables_to_restore)
    saver = tf.train.Saver(max_to_keep=max_to_keep) # selects how many snapshots are stored, see https://github.com/AlexEMG/DeepLabCut/issues/8#issuecomment-387404835

    sess = tf.Session()
    coord, thread = start_preloading(sess, enqueue_op, dataset, placeholders)
    train_writer = tf.summary.FileWriter(pose_cfg.log_dir, sess.graph)
    learning_rate, train_op = get_optimizer(total_loss, pose_cfg)

    sess.run(tf.global_variables_initializer())
    sess.run(tf.local_variables_initializer())

    # Restore variables from disk.
    restorer.restore(sess, pose_cfg.init_weights)
    if maxiters==None:
        max_iter = int(pose_cfg.multi_step[-1][1])
    else:
        max_iter = min(int(pose_cfg.multi_step[-1][1]),int(maxiters))
        #display_iters = max(1,int(displayiters))
        print("Max_iters overwritten as",max_iter)
    
    if displayiters==None:
        display_iters = max(1,int(pose_cfg.display_iters))
    else:
        display_iters = max(1,int(displayiters))
        print("Display_iters overwritten as",display_iters)
    
    if saveiters==None:
        save_iters=max(1,int(pose_cfg.save_iters))
        
    else:
        save_iters=max(1,int(saveiters))
        print("Save_iters overwritten as",save_iters)
        
    cum_loss = 0.0
    lr_gen = LearningRate(pose_cfg)
    validerror_min = float('inf')
    last_min = 0

    stats_path = Path(pose_config_yaml).with_name('learning_stats.csv')
    lrf = open(str(stats_path), 'w')
    imgs_path = Path(pose_config_yaml).parents[0] / 'imgs'
    try:
        imgs_path.mkdir(parents=True)
    except:
        pass
    from skimage import color
    print("Training parameter:")
    print(pose_cfg)
    print("Starting training....")
    for it in range(max_iter+1):
        current_lr = lr_gen.get_lr(it)
        [_, loss_val, summary, _inp, _outp, _targ] = sess.run([train_op, total_loss, merged_summaries,
                                           pose._inp, pose._outp, pose._targ],
                                          feed_dict={learning_rate: current_lr})
        cum_loss += loss_val
        train_writer.add_summary(summary, it)

        if it % display_iters == 0 and it>0:
            average_loss = cum_loss / display_iters
            cum_loss = 0.0
            logging.info("iteration: {} loss: {} lr: {}"
                         .format(it, "{0:.4f}".format(average_loss), current_lr))
            lrf.write("{}, {:.5f}, {}\n".format(it, average_loss, current_lr))
            lrf.flush()

            # save_img_gray(_inp[0, :, :, :] / 255, str('imgs/input' + str(it) + '.png'))
            # save_img_gray(_targ[0, :, :, 0], str('imgs/target' + str(it) + '.png'))
            # save_img_gray(_targ_locref[0, :, :, 0], str('imgs/locref_x' + str(it) + '.png'))
            # save_img_gray(_targ_locref[0, :, :, 1], str('imgs/locref_y' + str(it) + '.png'))
            # save_img_gray(_outp[0, :, :, 0], str('imgs/chat_predict' + str(it) + '.png'))

        # Save snapshot
        if (it % save_iters == 0 and it != 0) or it == max_iter:
            model_name = pose_cfg.snapshot_prefix
            print("Calculating validation performance...")
            validerror = validator.validate(sess, it)
            if validerror < validerror_min:
                validerror_min = validerror
                last_min = 0
                saver.save(sess, model_name, global_step=it)
            else:
                last_min += 1
                if last_min > early_stopping_thresh:
                    print("Early stopping because early_stopping_thresh has been exceeded.")
                    break
    lrf.close()
    validator.close()
    sess.close()
    coord.request_stop()
    coord.join([thread])
    #return to original path.
    os.chdir(str(start_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to yaml configuration file.')
    cli_args = parser.parse_args()

    train(Path(cli_args.config).resolve())
