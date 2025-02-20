from deeplabcut.pose_estimation_tensorflow.config import load_config
import modified.auxiliaryfunctions as auxiliaryfunctions
import os
from pathlib import Path


def change_setting_config(config_path, key, value):
    cfg = auxiliaryfunctions.read_config(config_path)
    cfg[key] = value
    auxiliaryfunctions.write_config(config_path, cfg)


def change_setting_train_config(config_path, key, value, trainingsetindex=0, shuffle=0):
    cfg = auxiliaryfunctions.read_config(config_path)
    modelfoldername = auxiliaryfunctions.GetModelFolder(cfg["TrainingFraction"][trainingsetindex], shuffle, cfg)
    path_train_config = str(os.path.join(cfg['project_path'], Path(modelfoldername), 'train', 'pose_cfg.yaml'))
    pose_cfg = load_config(path_train_config)
    auxiliaryfunctions.write_config(path_train_config, pose_cfg)

def change_setting_test_config(config_path, key, value, trainingsetindex=0, shuffle=0):
    cfg = auxiliaryfunctions.read_config(config_path)
    modelfoldername = auxiliaryfunctions.GetModelFolder(cfg["TrainingFraction"][trainingsetindex], shuffle, cfg)
    path_test_config = str(os.path.join(cfg['project_path'], Path(modelfoldername), 'test', 'pose_cfg.yaml'))
    pose_cfg = load_config(path_test_config)
    auxiliaryfunctions.write_config(path_test_config, pose_cfg)

