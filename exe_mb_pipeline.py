# -*- coding: utf-8 -*-

import os, sys
import subprocess
import json
import shutil

import utils
import marge_bart
from utils import model_logger as logger

sys.setrecursionlimit(20000)

# ======== load conf.yaml ========
# PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
# MARGE_DIR = ''
# BART_DIR = ''
# # default
# BART_CORE = 4 
# MARGE_CORE = 4 
# MARGE_REPEAT_TIMES = 3
# with open('conf.yaml', 'r') as fyaml:
#     try: 
#         conf_data = yaml.load(fyaml)
#         BART_DIR = conf_data['BART']['project_path']
#         MARGE_DIR = conf_data['MARGE']['project_path']

#         BART_CORE = conf_data['BART']['core']
#         MARGE_CORE = conf_data['MARGE']['core']
#         MARGE_REPEAT_TIMES = conf_data['MARGE']['repeat_times']
#     except yaml.YAMLError as e: 
#         print (e)

def main():
    # example: python exe_mb_pipline.py 3 user_key True/False
    # print (sys.argv)

    # get argv
    script_name = sys.argv[0]
    repeat_times = int(sys.argv[1])
    user_key = sys.argv[2]
    bart_flag = bool(sys.argv[3])

    import do_process
    user_data = do_process.get_user_data(user_key)
    user_path = user_data['user_path']
    files = user_data['files']

    err_msg = ""
    for i in range(repeat_times):
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        if marge_bart.init_marge(marge_output_dir):
            marge_bart.config_marge(user_data, marge_output_dir)
            subprocess.call(["snakemake", "-n"], stdout=subprocess.PIPE, cwd=marge_output_dir)
        else:
            err_msg += "Error in init marge NO.%d \n" % (i+1) 

    import multiprocessing
    pool = multiprocessing.Pool(processes=marge_bart.MARGE_CORE)
    for i in range(repeat_times):
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        pool.apply_async(marge_bart.exe_marge, args=(marge_output_dir, ))

    pool.close()
    pool.join() 

    # get marge output
    auc_scores = []
    auc_files = []
    import re
    pattern = r"\d+\.?\d*" # integer or float

    # find AUC score
    for i in range(repeat_times):
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        for upload_file in files:
            filename = os.path.basename(upload_file)
            filename, file_ext = os.path.splitext(filename)
            regression_score_file = os.path.join(marge_output_dir, 'margeoutput/regression/{}_target_regressionInfo.txt'.format(filename))

            if not os.path.exists(regression_score_file):
                err_msg += "File does not exist: %s" % (regression_score_file)
                continue
            
            with open(regression_score_file, 'r') as fopen:
                for line in fopen:
                    if 'AUC = ' in line:
                        score = re.findall(pattern, line)[0]
                        auc_scores.append(float(score))
                        auc_files.append(marge_output_dir)

    # find max AUC score
    max_auc = max(auc_scores)
    max_index = -1
    for i in range(len(auc_scores)):
        if auc_scores[i] == max_auc:
            max_index = i
            break

    # find max AUC folder & change it to folder /marge_data
    if max_index == -1:
        err_msg += "Severe error in marge process!!\n"
    else:
        auc_file = auc_files[i]
        os.rename(auc_file, os.path.join(user_path, 'marge_data'))

    # if bart
    logger.info(user_data)
    if bart_flag:
        marge_bart.exe_bart_geneset(user_data)

    logger.info(err_msg)


if __name__ == '__main__':
    main()
    