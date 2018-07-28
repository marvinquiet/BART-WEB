import os
import subprocess
import json
import shutil

import utils

PROJECT_DIR = os.path.dirname(__file__)
MARGE_DIR = os.path.join(PROJECT_DIR, "MARGE")

# init marge env
def init_marge(user_path):
    user_upload_path = os.path.join(user_path, 'upload')
    marge_output_dir = os.path.join(user_path, 'marge_data')
    marge_input_dir = user_upload_path

    # copy uploaded files into marge_output directory
    # src_files = os.listdir(marge_input_dir)
    # for file_name in src_files:
    #     full_file_name = os.path.join(marge_input_dir, file_name)
    #     if (os.path.isfile(full_file_name)):
    #         shutil.copy(full_file_name, marge_input_dir)

    # subprocess.call(["cd", MARGE_DIR])
    marge_res = subprocess.check_call(["marge", "init", marge_output_dir])
    if marge_res == 0:
        return True
    else:
        return False

# edit config.json
def config_marge(user_path, user_data):
    user_upload_path = os.path.join(user_path, 'upload')
    marge_output_dir = os.path.join(user_path, 'marge_data')
    marge_input_dir = user_upload_path

    # back up the original config.json
    config_file = os.path.join(marge_output_dir, 'config.json')
    config_file_bak = os.path.join(marge_output_dir, 'config.json.bak')
    shutil.copyfile(config_file, config_file_bak)

    with open(config_file) as data_file:
        data = json.load(data_file)

    # deal with the data into new config.json which will be used
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


def exe_marge(user_path):
    marge_output_dir = os.path.join(user_path, 'marge_data')
    user_log_path = os.path.join(user_path, 'log')

    res = subprocess.Popen(["snakemake", "-n"], stdout=subprocess.PIPE, cwd=marge_output_dir).communicate()

    # with open(os.path.join(user_log_path, 'snakemake_res.txt'), 'wb') as f_snake_res:
    #     f_snake_res.write(res[0])
    subprocess.Popen(["snakemake", "--cores", "1"], cwd=marge_output_dir)
    # print (res[0])


def is_marge_done(user_path):
    marge_output_dir = os.path.join(user_path, 'marge_data')
    snakemake_path = os.path.join(marge_output_dir, '.snakemake')
    snakemake_log_dir = os.path.join(snakemake_path, 'log')

    for log_file in os.listdir(snakemake_log_dir):
        if log_file.endswith(".log"):
            log_file_path = os.path.join(snakemake_log_dir, log_file)
            with open(log_file_path, 'rb') as file:
                for line in file:
                    if '(100%) done' in line:
                        return True
    return False









