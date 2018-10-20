# -*- coding: utf-8 -*-

import os, sys
import subprocess
import json
import yaml
import shutil

import do_process
import utils
from utils import model_logger as logger

sys.setrecursionlimit(20000)

# ======== load conf.yaml ========
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
MARGE_DIR = ''
BART_DIR = ''
# default
BART_CORE = 4 
MARGE_CORE = 4 
MARGE_REPEAT_TIMES = 3
# change to absolute path
with open(os.path.join(PROJECT_DIR, 'conf.yaml'), 'r') as fyaml:
    try: 
        conf_data = yaml.load(fyaml)
        BART_DIR = conf_data['BART']['project_path']
        MARGE_DIR = conf_data['MARGE']['project_path']
        MARGE_LIB_DIR = conf_data['MARGE']['lib_path']

        BART_CORE = conf_data['BART']['core']
        MARGE_CORE = conf_data['MARGE']['core']
        MARGE_REPEAT_TIMES = conf_data['MARGE']['repeat_times']

        MACS2_path = conf_data['UCSC_tools']['MACS2']
        bedClip_path = conf_data['UCSC_tools']['bedClip']
        bedGraphToBigWig_path = conf_data['UCSC_tools']['bedGraphToBigWig']
        bigWigAverageOverBed_path = conf_data['UCSC_tools']['bigWigAverageOverBed']
        bigWigSummary_path = conf_data['UCSC_tools']['bigWigSummary'] 
    except yaml.YAMLError as e: 
        print (e)

# ============ MARGE ==============

# init marge env
def init_marge(marge_output_dir):
    logger.info("Exe cmd: marge init {}".format(marge_output_dir))
    marge_res = subprocess.check_call(["marge", "init", marge_output_dir])
    if marge_res == 0:
        return True
    else:
        return False

# edit marge config.json
def config_marge(user_data, marge_output_dir):
    user_path = user_data['user_path']
    marge_input_dir = os.path.join(user_path, 'upload')

    # back up the original config.json
    config_file = os.path.join(marge_output_dir, 'config.json')
    config_file_bak = os.path.join(marge_output_dir, 'config.json.bak')
    shutil.copyfile(config_file, config_file_bak)

    with open(config_file) as data_file:
        data = json.load(data_file)

    # tools path in MARGE/config.json
    data["tools"]["MACS2"] = MACS2_path
    data["tools"]["bedClip"] = bedClip_path
    data["tools"]["bedGraphToBigWig"] = bedGraphToBigWig_path
    data["tools"]["bigWigAverageOverBed"] = bigWigAverageOverBed_path
    data["tools"]["bigWigSummary"] = bigWigSummary_path

    data["ASSEMBLY"] = user_data["assembly"]
    data["MARGEdir"] = os.path.join(MARGE_DIR, "marge")
    data["REFdir"] = os.path.join(MARGE_LIB_DIR, data["ASSEMBLY"] + "_all_reference")
    
    if user_data['dataType'] == "Geneset":
        data["SAMPLESDIR"] = ""
        data["SAMPLES"] = ""
        data["EXPSDIR"] = marge_input_dir
        data["EXPS"] = utils.get_files_in_dir("GeneList", data["EXPSDIR"])
        # Gene_Only & Gene_Response
        # data["EXPTYPE"] = user_data["gene_exp_type"]  
        data["EXPTYPE"] = 'Gene_Only'
        # GeneSymbol & RefSeq
        # data["ID"] = user_data["gene_id_type"]
        data["ID"] = 'GeneSymbol'

    with open(config_file, 'w') as data_file:
        json.dump(data, data_file)

def exe_marge(marge_output_dir):
    cmd = "snakemake --cores {}".format(str(MARGE_CORE))
    logger.info("Exe cmd: " + cmd)
    subprocess.call(cmd, cwd=marge_output_dir, stdout=subprocess.PIPE)
    # subprocess.call(["snakemake", "--cores", str(MARGE_CORE)], cwd=marge_output_dir, stdout=subprocess.PIPE)

def is_marge_done(user_path):
    snakemake_log_dir = os.path.join(user_path, 'marge_data/.snakemake/log')
    if not os.path.exists(snakemake_log_dir):
        return False

    for log_file in os.listdir(snakemake_log_dir):
        if log_file.endswith(".log"):
            log_file_path = os.path.join(snakemake_log_dir, log_file)
            with open(log_file_path, 'r') as flog:
                if ('(100%) done') not in flog.read():
                    return False
    return True

def get_enhancer_prediction(user_path):
    # marge output file path
    eh_files = []
    eh_files_path = os.path.join(user_path, 'marge_data/margeoutput/cisRegions')
    for eh_file in os.listdir(eh_files_path):
        if '_enhancer_prediction.txt' in str(eh_file):
            eh_files.append(os.path.join(eh_files_path, eh_file))

    return eh_files

# ============ BART ==============

def exe_bart_profile(user_data):
    '''
    Usage:
    bart profile [-h] <-i infile> <-f format> <-s species> [-t target] [-p processes] [--outdir] [options]

    Example:

    bart profile -i ChIP.bed/ChIP.bam -f bed/bam -s hg38 -t target.txt -p 4 --outdir bart_output
    '''
    bart_output_path = os.path.join(user_data['user_path'], 'download/bart_output')
    for input_file in user_data['files']:
        if input_file.endswith(".bam"):
            cmd = "bart profile -i {} -f bam -s {} -p {} --outdir {}".format(input_file, user_data["assembly"], str(BART_CORE), bart_output_path)
            logger.info("Exe cmd: " + cmd)
            subprocess.call(cmd, cwd=bart_output_path)
            # subprocess.Popen(["bart", "profile", "-i", input_file, "-f", "bam", "-s", user_data["assembly"], "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)
        elif input_file.endswith(".bed"):
            cmd = "bart profile -i {} -f bed -s {} -p {} --outdir {}".format(input_file, user_data["assembly"], str(BART_CORE), bart_output_path)
            logger.info("Exe cmd: " + cmd)
            subprocess.call(cmd, cwd=bart_output_path)
            # subprocess.Popen(["bart", "profile", "-i", input_file, "-f", "bed", "-s", user_data["assembly"], "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)


def exe_bart_geneset(user_data):
    '''
    Usage:
    bart geneset [-h] <-i infile> <-s species> [-t target] [-p processes] [--outdir] [options]

    Example:

    bart geneset -i name_enhancer_prediction.txt -s hg38 -t target.txt -p 4 --outdir bart_output
    '''
    bart_output_path = os.path.join(user_data['user_path'], 'download/bart_output')
    eh_files = get_enhancer_prediction(user_data['user_path'])
    for eh_file in eh_files:
        cmd = "bart geneset -i {} -s {} -p {} --outdir {}".format(eh_file, user_data["assembly"], str(BART_CORE), bart_output_path)
        logger.info("Exe cmd: " + cmd)
        # subprocess.call(["bart", "geneset", "-i", eh_file, "-s", user_data["assembly"], "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)
        subprocess.call(cmd, cwd=bart_output_path)


def is_bart_done(user_path):
    user_key = os.path.basename(user_path)
    user_data = do_process.get_user_data(user_key)
    for user_file in user_data['files']:
        uploaded_file = os.path.basename(user_file).split('.')[0] # path/to/user/upload/filename.bam(txt)
        res_file_path = os.path.join(user_path, 'download/bart_output/' + uploaded_file + '_bart_results.txt') # path/to/user/download/filename_bart_results.txt
        if not os.path.exists(res_file_path):
            return False
    
    return True


# ========= MARGE BART PIPELINE =========
# call file in background to execute pipeline, otherwise, it will block the web server

# slurm project dir
SLURM_PROJECT_DIR = '/sfs/qumulo/qproject/CPHG/BART'   # hard-code path 
DOCKER_DIR = '/var/www/apache-flask'

def do_marge_bart(user_data):
    # write slurm
    user_path = user_data['user_path']
    user_key = user_data['user_key']
    # user_path = SLURM_PROJECT_DIR + '/usercase/' + user_key
    slurm_file = os.path.join(user_path, 'exe.slurm')

    logger.info("Write slurm: write {} data to {}...".format(user_key, slurm_file))
    logger.info("Write slurm: change docker path to rivanna path...")
    # change user path
    new_user_path = user_data['user_path'].replace(DOCKER_DIR, SLURM_PROJECT_DIR)
    user_data['user_path'] = new_user_path
    do_process.init_user_config(user_path, user_data)

    with open(slurm_file, 'w') as fopen:
        fopen.write('''#!/bin/bash
#SBATCH -n 1
#SBATCH --mem=100000
#SBATCH -t 48:00:00
#SBATCH -p standard
#SBATCH -A zanglab
source ~/.bashrc
#Run program\n''')
        # pipeline script
        script_file = os.path.join(SLURM_PROJECT_DIR, 'exe_mb_pipeline.py')
        # bart result plot script
        bart_plot_file = os.path.join(SLURM_PROJECT_DIR, 'bart_plot.py')
        marge_bart_script = os.path.join(SLURM_PROJECT_DIR, 'marge_bart.py')
        slurm_user_path = SLURM_PROJECT_DIR + '/usercase/' + user_key
        exe_log_path = os.path.join(slurm_user_path, 'log/mb_pipe.log')

        if user_data['bart'] and user_data['marge']:
            cmd = 'python ' + script_file + ' 3 ' + user_key + ' True  > ' + exe_log_path + ' 2>&1 && \\ \n'
            logger.info("Write slurm: " + cmd)
            fopen.write(cmd)

            cmd = 'python ' + bart_plot_file + ' ' + user_key +  '  >> ' + exe_log_path + ' 2>&1 && \\ \n'
            logger.info("Write slurm: " + cmd)
            fopen.write(cmd)

        if user_data['bart'] and not user_data['marge']:
            bart_output_path = os.path.join(slurm_user_path, 'download')
            plot_flag = False
            for input_file in user_data['files']:
                input_file_path = os.path.join(slurm_user_path, 'upload/' + input_file)
                if input_file.endswith(".bam"):
                    cmd = 'bart profile -i ' + input_file_path + ' -f bam -s ' + user_data["assembly"] + ' -p ' + str(BART_CORE) + ' --outdir ' + bart_output_path + '  > ' + exe_log_path + ' 2>&1 && \\ \n'
                    logger.info("Write slurm: " + cmd)
                    fopen.write(cmd)

                    plot_flag = True # at least there are some result files being generated by bart
                elif input_file.endswith(".bed"):
                    cmd = 'bart profile -i ' + input_file_path + ' -f bed -s ' + user_data["assembly"] + ' -p ' + str(BART_CORE) + ' --outdir ' + bart_output_path + '  > ' + exe_log_path + ' 2>&1 && \\ \n'
                    logger.info("Write slurm: " + cmd)
                    fopen.write(cmd)

                    plot_flag = True # at least there are some result files being generated by bart
                
            if plot_flag:
                cmd = 'python ' + bart_plot_file + ' ' + user_key +  '  >> ' + exe_log_path + ' 2>&1 && \\ \n'
                logger.info("Write slurm: " + cmd)
                fopen.write(cmd)
        
        # change back the user.config to what Docker could recognize
        cmd = 'python ' + marge_bart_script + ' ' + user_key + ' >> ' + exe_log_path + ' 2>&1\n'
        logger.info("Write slurm: " + cmd)
        fopen.write(cmd)

    
# ============== UNIT TEST ===============
def test_is_marge_done():
    test_path = '/Users/marvin/Projects/flask_playground/usercase/a_1534972940.637962'
    assert is_marge_done(test_path) == True


# change user.config
def main():
    # python marge_bart.py user_key
    # get argv
    script_name = sys.argv[0]
    user_key = sys.argv[1]

    import do_process
    import yaml

    # get user data
    user_data = do_process.get_user_data(user_key)
    user_path = user_data['user_path']
    logger.info("Job Finish: clean up the data for {}...".format(user_key))
    if 'status' in user_data and user_data['status'] == 'Error':
        logger.error("Job Finish: user {} job error, check log!".format(user_key))
        return

    logger.info("Job Check: whether job succeeded... ")
    logger.info("Job Finish: change user.config path to docker... ")
    logger.info("Job Finish: change user.config status to Done... ")
    new_user_path = user_path.replace(SLURM_PROJECT_DIR, DOCKER_DIR)
    user_data['user_path'] = new_user_path
    user_data['status'] = 'Done'
    do_process.init_user_config(user_path, user_data)

    # delete user in queue
    usercase_dir = os.path.dirname(user_path)
    user_queue_file = os.path.join(usercase_dir, 'user_queue.yaml')
    with open(user_queue_file, 'r') as fqueue:
        queue_data = yaml.load(fqueue)

    logger.info("Job Finish: delete user in queue... ")
    if queue_data and user_key in queue_data: # delete the user whose job is done
        logger.info("Job Finish: Delete {} successfully...".format(user_key))
        del queue_data[user_key]
    else:
        logger.error('Job Finish: User {} not in queue! Please check!'.format(user_key))

    
    with open(user_queue_file, 'w') as fqueue:
        logger.info("Job Finish: save to user queue... ")
        if len(queue_data) > 0:
            yaml.dump(queue_data, fqueue, default_flow_style=False)


if __name__ == '__main__':
    main()
    