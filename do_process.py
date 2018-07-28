import os
import subprocess
import shutil
import json

import utils

PROJECT_DIR = os.path.dirname(__file__)

def generate_user_key(username):
    import time
    tstamp = time.time()
    key = username + '_' + str(tstamp)
    return key

def init_project_path(user_key):
    user_path = os.path.join(PROJECT_DIR, user_key)
    user_upload_path = os.path.join(user_path, 'upload')
    user_download_path = os.path.join(user_path, 'download')
    user_log_path = os.path.join(user_path, 'log')

    utils.create_dir(user_path)
    utils.create_dir(user_upload_path)
    utils.create_dir(user_download_path)
    utils.create_dir(user_log_path)

    return user_path


def init_user_config(user_path, user_data):
    # init username.config and save config data
    config_file = os.path.join(user_path, 'user.config')
    with open(config_file, 'wb') as fopen:
        fopen.write(json.dumps(user_data))

def get_user_data(user_key):
    user_path = os.path.join(PROJECT_DIR, user_key)
    config_file = os.path.join(user_path, 'user.config')
    with open(config_file, 'rb') as fopen:
        user_data = json.load(fopen)

    return user_data

def is_user_key_exists(user_key):
    dest_path = os.path.join(PROJECT_DIR, user_key)
    return os.path.exists(dest_path)













