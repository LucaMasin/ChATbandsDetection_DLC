import os
from os.path import split, splitext
import pandas as pd
from chatbands import tifstack_2_avi
import cv2
#from tifffile import imsave
import imageio
import numpy as np

def get_slice_results(tif_path, data_path, dest_path, step_size=20):

    tif_dir, tif = split(tif_path)
    video = tifstack_2_avi.get_video(tif_path)*255
    length, height, width = video.shape
    # tifstack_2_avi.play_video(video, 5)
    # tif_name, ext = splitext(tif)
    # data_dir, data = split(data_path)
    # data_file = [f for f in os.listdir(path) if f.startswith(name) and f.endswith('.h5')][0]

    df = pd.read_hdf(data_path)
    res_list = []
    pos = 0
    frame = 0
    prev_ON = None
    prev_OFF = None
    for i, row in df.iterrows():
        res_list.append([frame, pos, row[:, 'ON', 'y'].values[0], row[:, 'ON', 'likelihood'].values[0], row[:, 'OFF', 'y'].values[0], row[:, 'OFF', 'likelihood'].values[0]])
        if row[:, 'ON', 'likelihood'].values[0] >= 0.0:
            ON = row[:, 'ON', 'y']
            cv2.circle(video[frame], (pos, ON), 3, (255, 0, 0), -1)
            if prev_ON is not None:
                cv2.line(video[frame], prev_ON, (pos, ON), (255, 0, 0), thickness=2)
            prev_ON = (pos, ON)
        if row[:, 'OFF', 'likelihood'].values[0] >= 0.0:
            OFF = row[:, 'OFF', 'y']
            cv2.circle(video[frame], (pos, OFF), 3, (255, 120, 0), -1)

            if prev_OFF is not None:
                cv2.line(video[frame], prev_OFF, (pos, OFF), (255, 120, 0), thickness=2)
            prev_OFF = (pos, OFF)
        pos += step_size
        if pos > width:
            frame += 1
            pos = 0
            prev_ON = None
            prev_OFF = None
    print(type(np.uint8(video)[0, 0, 0]))
    res = pd.DataFrame(res_list, columns=['Slice', 'X', 'Y_ON', 'P_ON', 'Y_OFF', 'P_OFF'])
    res.to_csv(os.path.join(dest_path, 'result_{}.csv'.format(tif.split('.')[0])))
    tifstack_2_avi.data_2_mp4(video, os.path.join(dest_path, 'resultvideo_{}'.format(tif.split('.')[0])), 60)
    imageio.mimwrite(os.path.join(dest_path, 'resulttif_{}.tif'.format(tif.split('.')[0])), np.uint8(video))