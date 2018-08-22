import os, sys
import subprocess
import json
import shutil

import utils

sys.setrecursionlimit(20000)

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
MARGE_DIR = os.path.join(PROJECT_DIR, "MARGE")
BART_DIR = os.path.join(PROJECT_DIR, "BART")

BART_CORE = 1
MARGE_CORE = 4
REPEAT_TIMES = 1

# =============MARGE===============

# init marge env
def init_marge(marge_output_dir):
    # subprocess.call(["cd", MARGE_DIR])
    marge_res = subprocess.check_call(["marge", "init", marge_output_dir])
    if marge_res == 0:
        return True
    else:
        return False

# edit config.json
def config_marge(user_data, marge_output_dir):

    user_path = user_data['user_path']
    marge_input_dir = os.path.join(user_path, 'upload')

    # back up the original config.json
    config_file = os.path.join(marge_output_dir, 'config.json')
    config_file_bak = os.path.join(marge_output_dir, 'config.json.bak')
    shutil.copyfile(config_file, config_file_bak)

    with open(config_file) as data_file:
        data = json.load(data_file)

    # TODO: deal with the data into new config.json which will be used
    data["tools"]["MACS2"] = "/usr/local/Cellar/pyenv/1.2.1/versions/venv2.7/bin/macs2"

    marge_tools_dir = os.path.join(MARGE_DIR, "marge_ucsc_tools")
    data["tools"]["bedClip"] = os.path.join(marge_tools_dir, "bedClip")
    data["tools"]["bedGraphToBigWig"] = os.path.join(marge_tools_dir, "bedGraphToBigWig")
    data["tools"]["bigWigAverageOverBed"] = os.path.join(marge_tools_dir, "bigWigAverageOverBed")
    data["tools"]["bigWigSummary"] = os.path.join(marge_tools_dir, "bigWigSummary")

    data["ASSEMBLY"] = user_data["assembly"]
    data["MARGEdir"] = os.path.join(MARGE_DIR, "marge")
    marge_ref_dir = os.path.join(MARGE_DIR, "marge_ref")
    data["REFdir"] = os.path.join(marge_ref_dir, data["ASSEMBLY"] + "_all_reference")

    if user_data['dataType'] == "ChIP-seq":
        data["EXPSDIR"] = ""
        data["EXPS"] = ""
        data["EXPTYPE"] = ""
        data["ID"] = ""
        data["SAMPLESDIR"] = marge_input_dir
        data["SAMPLES"] = utils.get_files_in_dir("ChIP", data["SAMPLESDIR"])
    elif user_data['dataType'] == "Geneset":
        data["SAMPLESDIR"] = ""
        data["SAMPLES"] = ""
        data["EXPSDIR"] = marge_input_dir
        data["EXPS"] = utils.get_files_in_dir("GeneList", data["EXPSDIR"])
        # Gene_Only & Gene_Response
        data["EXPTYPE"] = user_data["gene_exp_type"]  
        # GeneSymbol & RefSeq
        data["ID"] = user_data["gene_id_type"]
    elif user_data['dataType'] == "Both":
        data["SAMPLESDIR"] = marge_input_dir
        data["EXPSDIR"] = marge_input_dir
        data["SAMPLES"] = utils.get_files_in_dir("ChIP", data["SAMPLESDIR"])
        data["EXPS"] = utils.get_files_in_dir("GeneList", data["EXPSDIR"])
        # Gene_Only & Gene_Response
        data["EXPTYPE"] = user_data["gene_exp_type"]  
        # GeneSymbol & RefSeq
        data["ID"] = user_data["gene_id_type"]

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
            with open(log_file_path, 'r') as file:
                for line in file:
                    if '(100%) done' in line:
                        return True
    return False

# =============BART===============

def exe_bart_profile(user_data):
    '''
    Usage:
    bart profile [-h] <-i infile> <-f format> <-s species> [-t target] [-p processes] [--outdir] [options]

    Example:

    bart profile -i ChIP.bed -f bed -s hg38 -t target.txt -p 4 --outdir bart_output
    '''
    bart_output_path = os.path.join(user_data['user_path'], 'download')
    target_file_path = os.path.join(BART_DIR, 'BART/{assembly_type}_library/{assembly_type}_test_data/target.txt'.format(assembly_type=user_data["assembly"]))

    for input_file in user_data['files']:
        if input_file.endswith(".bam"):
            subprocess.Popen(["bart", "profile", "-i", input_file, "-f", "bam", "-s", user_data["assembly"], "-t", target_file_path, "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)

def exe_bart_geneset(user_data):
    '''
    Usage:
    bart geneset [-h] <-i infile> <-s species> [-t target] [-p processes] [--outdir] [options]

    Example:

    bart geneset -i name_enhancer_prediction.txt -s hg38 -t target.txt -p 4 --outdir bart_output
    '''
    bart_output_path = os.path.join(user_data['user_path'], 'download')
    target_file_path = os.path.join(BART_DIR, 'BART/{assembly_type}_library/{assembly_type}_test_data/target.txt'.format(assembly_type=user_data["assembly"]))
    
    eh_files = get_enhancer_prediction(user_data['user_path'])
    for eh_file in eh_files:
        subprocess.Popen(["bart", "geneset", "-i", eh_file, "-s", user_data["assembly"], "-t", target_file_path, "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)

def get_enhancer_prediction(user_path):
    # marge output file path
    eh_files = []
    eh_files_path = os.path.join(user_path, 'marge_data/margeoutput/cisRegions')
    for eh_file in os.listdir(eh_files_path):
        if '_enhancer_prediction.txt' in str(eh_file):
            eh_files.append(os.path.join(eh_files_path, eh_file))

    return eh_files

# ==========MARGE+BART==========

def do_marge_bart(user_key, bart_flag):
    subprocess.Popen(["python", "marge_bart.py", str(REPEAT_TIMES), user_key, str(bart_flag)], cwd=PROJECT_DIR)

if __name__ == '__main__':
    # python do_marge.py 3 marge_output_dir
    # print (sys.argv)
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
        if init_marge(marge_output_dir):
            config_marge(user_data, marge_output_dir)
            subprocess.call(["snakemake", "-n"], stdout=subprocess.PIPE, cwd=marge_output_dir)
        else:
            err_msg += "Error in init marge NO.%d \n" % (i+1) 

    import multiprocessing
    pool = multiprocessing.Pool(processes=MARGE_CORE)
    for i in range(repeat_times):
        marge_output_dir = os.path.join(user_path, 'marge_{}'.format(i))
        pool.apply_async(exe_marge, args=(marge_output_dir, ))

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
                err_msg += "File not exists: %s" % (regression_score_file)
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
    if bart_flag:
        exe_bart_geneset(user_data)

    print (err_msg)

    

    
    


                    




