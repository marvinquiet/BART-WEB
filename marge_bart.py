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
        conf_data = yaml.safe_load(fyaml)
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
    # subprocess.call(["cd", MARGE_DIR])
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

    # if user_data['dataType'] == "ChIP-seq":
    #     data["EXPSDIR"] = ""
    #     data["EXPS"] = ""
    #     data["EXPTYPE"] = ""
    #     data["ID"] = ""
    #     data["SAMPLESDIR"] = marge_input_dir
    #     data["SAMPLES"] = utils.get_files_in_dir("ChIP", data["SAMPLESDIR"])
    
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

    # elif user_data['dataType'] == "Both":
    #     data["SAMPLESDIR"] = marge_input_dir
    #     data["EXPSDIR"] = marge_input_dir
    #     data["SAMPLES"] = utils.get_files_in_dir("ChIP", data["SAMPLESDIR"])
    #     data["EXPS"] = utils.get_files_in_dir("GeneList", data["EXPSDIR"])
    #     # Gene_Only & Gene_Response
    #     data["EXPTYPE"] = user_data["gene_exp_type"]  
    #     # GeneSymbol & RefSeq
    #     data["ID"] = user_data["gene_id_type"]

    with open(config_file, 'w') as data_file:
        json.dump(data, data_file)

def exe_marge(marge_output_dir):
    subprocess.call(["snakemake", "--cores", str(MARGE_CORE)], cwd=marge_output_dir, stdout=subprocess.PIPE)

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

    bart profile -i ChIP.bed -f bed -s hg38 -t target.txt -p 4 --outdir bart_output
    '''
    bart_output_path = os.path.join(user_data['user_path'], 'download/bart_output')
    for input_file in user_data['files']:
        if input_file.endswith(".bam"):
            subprocess.Popen(["bart", "profile", "-i", input_file, "-f", "bam", "-s", user_data["assembly"], "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)
        elif input_file.endswith(".bed"):
            subprocess.Popen(["bart", "profile", "-i", input_file, "-f", "bed", "-s", user_data["assembly"], "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)


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
        subprocess.call(["bart", "geneset", "-i", eh_file, "-s", user_data["assembly"], "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)

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

def do_marge_bart(user_data):
    # write slurm
    user_path = user_data['user_path']
    user_key = user_data['user_key']
    # user_path = SLURM_PROJECT_DIR + '/usercase/' + user_key
    slurm_file = os.path.join(user_path, 'exe.slurm')
    with open(slurm_file, 'w') as fopen:
        fopen.write('''#!/bin/bash
#SBATCH -n 1
#SBATCH --mem=100000
#SBATCH -t 48:00:00
#SBATCH -p standard
#SBATCH -A zanglab
source ~/.bashrc
module load anaconda3
#Run program\n''')
        # pipeline script
        script_file = os.path.join(SLURM_PROJECT_DIR, 'exe_mb_pipeline.py')
        # bart result plot script
        bart_plot_file = os.path.join(SLURM_PROJECT_DIR, 'bart_plot.py')
        slurm_user_path = SLURM_PROJECT_DIR + '/usercase/' + user_key
        exe_log_path = os.path.join(slurm_user_path, 'log/mb_pipe.log')
        if user_data['bart'] and user_data['marge']:
            fopen.write('python ' + script_file + ' 3 ' + user_key + ' True  > ' + exe_log_path + ' 2>&1\n')
            fopen.write('python ' + bart_plot_file + ' ' + user_key +  '  >> ' + exe_log_path + ' 2>&1\n')
            return
        
        if not user_data['bart'] and user_data['marge']:
            fopen.write('python ' + script_file + ' 3 ' + user_key + ' False  > ' + exe_log_path + ' 2>&1\n')
            fopen.write('python ' + bart_plot_file + ' ' + user_key +  '  >> ' + exe_log_path + ' 2>&1\n')
            return

        if user_data['bart'] and not user_data['marge']:
            bart_output_path = os.path.join(slurm_user_path, 'download')
            plot_flag = False
            for input_file in user_data['files']:
                if input_file.endswith(".bam"):
                    fopen.write('bart profile -i ' + input_file + ' -f bam -s ' + user_data["assembly"] + ' -p ' + str(BART_CORE) + ' --outdir ' + bart_output_path + '  > ' + exe_log_path + ' 2>&1\n')
                    plot_flag = True # at least there are some result files being generated by bart
                elif input_file.endswith(".bed"):
                    fopen.write('bart profile -i ' + input_file + ' -f bed -s ' + user_data["assembly"] + ' -p ' + str(BART_CORE) + ' --outdir ' + bart_output_path + '  > ' + exe_log_path + ' 2>&1\n')
                    plot_flag = True # at least there are some result files being generated by bart
                
            if plot_flag:
                fopen.write('python ' + bart_plot_file + ' ' + user_key +  '  >> ' + exe_log_path + ' 2>&1\n')

    # after writing to slurm, change the path inside user.config to what rivanna could read
    revise_user_config(user_key, user_path)

DOCKER_DIR = '/var/www/apache-flask/'
RIVANNA_DIR = '/sfs/qumulo/qproject/CPHG/BART/'
def revise_user_config(user_key, user_path):
    user_data = do_process.get_user_data(user_key)
    user_data['user_path'] = user_data['user_path'].replace(DOCKER_DIR, RIVANNA_DIR)

    new_file_path = []
    for file_path in user_data['files']:
        new_file_path.append(file_path.replace(DOCKER_DIR, RIVANNA_DIR))
    user_data['files'] = new_file_path

    do_process.init_user_config(user_path, user_data)
    
# ============== UNIT TEST ===============
def test_is_marge_done():
    test_path = '/Users/marvin/Projects/flask_playground/usercase/a_1534972940.637962'
    assert is_marge_done(test_path) == True


if __name__ == '__main__':
    test_is_marge_done()