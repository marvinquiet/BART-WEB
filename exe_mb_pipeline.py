# -*- coding: utf-8 -*-

import os, sys
import time
import subprocess
import json
import shutil

import utils
import marge_bart
from utils import model_logger as logger

sys.setrecursionlimit(20000)

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

    logger.info("Pipeline Start: {}... ".format(user_key))

    for i in range(repeat_times):
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        logger.info("Pipeline Marge: init marge in {} ...".format(marge_output_dir))
        if marge_bart.init_marge(marge_output_dir):
            logger.info("Pipeline Marge: config marge config.json ...")
            marge_bart.config_marge(user_data, marge_output_dir)
            subprocess.call(["snakemake", "-n"], stdout=subprocess.PIPE, cwd=marge_output_dir)
        else:
            logger.error("Pipeline Marge: error in initing marge %d !"%(i+1))
            return  # will not execute anymore

    # multiprocessing for marge
    import multiprocessing

    jobs = []
    logger.info("Pipeline Marge: execute marge... ")
    for i in range(repeat_times):
        # time.sleep(30) 
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        p = multiprocessing.Process(target=marge_bart.exe_marge, args=(marge_output_dir, ))
        jobs.append(p)
        p.start()

    for job in jobs:
        job.join()

    # get marge output
    auc_scores = []
    auc_files = []
    import re
    pattern = r"\d+\.?\d*" # integer or float

    # find AUC score in marge output
    for i in range(repeat_times):
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        for upload_file in files:
            filename = os.path.basename(upload_file)
            filename, file_ext = os.path.splitext(filename)
            regression_score_file = os.path.join(marge_output_dir, 'margeoutput/regression/{}_target_regressionInfo.txt'.format(filename))
            if not os.path.exists(regression_score_file):
                logger.error("Pipeline Marge: {} does not exist".format(regression_score_file))
                continue

            enhancer_prediction_file = os.path.join(marge_output_dir, 'margeoutput/cisRegions/{}_enhancer_prediction.txt'.format(filename))
            if not os.path.exists(enhancer_prediction_file) or os.stat(enhancer_prediction_file).st_size == 0:
                logger.error("Pipeline Marge: {} does not exist".format(enhancer_prediction_file))
                continue

            with open(regression_score_file, 'r') as fopen:
                for line in fopen:
                    if 'AUC = ' in line:
                        score = re.findall(pattern, line)[0]
                        auc_scores.append(float(score))
                        auc_files.append(marge_output_dir)

    # whether marge generated results
    if len(auc_files) == 0 or len(auc_scores) == 0:
        logger.error("Pipeline Marge: error executing marge !")
        logger.error("Pipeline Marge: check marge for user {}!".format(user_key))
        return

    # find max AUC score
    max_auc = max(auc_scores)
    max_index = -1
    for i in range(len(auc_scores)):
        if auc_scores[i] == max_auc:
            max_index = i
            break

    # find max AUC folder & change it to folder /marge_data
    logger.info("Pipeline Marge: marge successfully done for {}...".format(user_key))
    logger.info("Pipeline Marge: find the one with max auc and change it to marge_data ...")
    auc_file = auc_files[max_index]
    os.rename(auc_file, os.path.join(user_path, 'marge_data'))

    logger.info("Pipeline Marge: copy marge_data to download directory...")

    # if bart
    if bart_flag:
        logger.info("Pipeline Bart: Start executing bart...")
        marge_bart.exe_bart_geneset(user_data)


if __name__ == '__main__':
    main()
