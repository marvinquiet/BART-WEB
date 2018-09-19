import os
import subprocess
import shutil
import json

import utils
import marge_bart

PROJECT_DIR = os.path.dirname(__file__)

def generate_user_key(username):
    import time
    tstamp = time.time()
    key = username + '_' + str(tstamp)
    return key

def init_project_path(user_key):
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
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
    with open(config_file, 'w') as fopen:
        json.dump(user_data, fopen)


def get_user_data(user_key):
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    config_file = os.path.join(user_path, 'user.config')
    with open(config_file, 'r') as fopen:
        user_data = json.load(fopen)

    return user_data

def is_user_key_exists(user_key):
    dest_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    return os.path.exists(dest_path)


def config_results(results, user_data):
    # user config
    results['user_conf'] = {}
    results['user_conf']['YourKey'] = user_data['user_key']
    results['user_conf']['Assembly'] = user_data['assembly']
    results['user_conf']['DataType'] = user_data['dataType']
    if user_data['gene_exp_type'] != "":
        results['user_conf']['GeneExpressionType'] = user_data['gene_exp_type']
    if user_data['gene_id_type'] != "":
        results['user_conf']['GeneIdType'] = user_data['gene_id_type']

    results['user_conf']['PredictionType'] = []
    if 'rp' in user_data['prediction_type']:
        results['user_conf']['PredictionType'].append("Relative Potentials")
    if 'cis' in user_data['prediction_type']:
        results['user_conf']['PredictionType'].append("Cisregulatory Elements")
    if 'tf' in user_data['prediction_type']:
        results['user_conf']['PredictionType'].append("TF patterns")
    if 'eh' in user_data['prediction_type']:
        results['user_conf']['PredictionType'].append("Enhancer")

    results['user_conf']['UploadFiles'] = []
    for file_path in user_data['files']:
        results['user_conf']['UploadFiles'].append(str(file_path.split('/')[-1]))


def generate_results(user_data):
    results = {}
    config_results(results, user_data)
    results['done'] = True

    # dataType: ChIP-seq, Geneset, Both
    # prediction_type: rp, cis, tf, eh
    # assembly: hg38, mm10
    # gene_exp_type: Gene_Only, Gene_Response
    # gene_id_type: GeneSymbol, RefSeq

    

    # only use bart to process
    if 'tf' in user_data['prediction_type'] and user_data['dataType'] == "ChIP-seq":
        
        return results

    # use only marge to process
    if marge_bart.is_marge_done(user_data['user_path']):
        # marge procedure log file path
        results['proc_log'] = []
        snakemake_log_dir = os.path.join(user_data['user_path'], 'marge_data/.snakemake/log')
        
        for log_file in os.listdir(snakemake_log_dir):
            if log_file.endswith(".log"):
                src_log = os.path.join(snakemake_log_dir, log_file)
                dest_log = os.path.join(user_data['user_path'], 'download/' + log_file)
                shutil.copyfile(src_log, dest_log)
                
                log_file_url = '/download/%s___%s' % (user_data['user_key'], log_file)
                results['proc_log'].append((log_file, log_file_url))

        # marge output file path
        marge_output_path = os.path.join(user_data['user_path'], 'marge_data/margeoutput')
        results['result_files'] = []
        suffix_type = ['_enhancer_prediction.txt', '_all_relativeRP.txt', '_Strength.txt', '_all_RP.txt', '_target_regressionInfo.txt']
        for root, dirs, files in os.walk(marge_output_path):
            for file in files:
                for file_type in suffix_type:
                    if file_type in str(file):
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(user_data['user_path'], 'download/' + file)
                        shutil.copyfile(src_file, dest_file)

                        dest_file_url = '/download/%s___%s' % (user_data['user_key'], file)
                        results['result_files'].append((file, dest_file_url))




        results['bartResult'] = parse_bart_results('/Users/marvin/Projects/flask_playground/usercase/a_1534972940.637962/download/genelist1_bart_results.txt')

        return results

    # marge does not finish
    results['processing_log'] = ""
    snakemake_log_dir = os.path.join(user_data['user_path'], 'marge_data/.snakemake/log')
    if not os.path.exists(snakemake_log_dir):
        results['done'] = False
        return results
        
    for log_file in os.listdir(snakemake_log_dir):
        if log_file.endswith(".log"):
            log_file_path = os.path.join(snakemake_log_dir, log_file)
            template_path = os.path.join(PROJECT_DIR, 'template')
            results['processing_log'] = os.path.relpath(log_file_path, template_path)
    return results  



def parse_bart_results(bart_result_file):
    # tf_name, tf_score, p_value, z_score, max_auc, r_rank -> definition in result_demonstration.html
    bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank'] 
    bart_result = []
    with open(bart_result_file, 'r') as fopen:
        next(fopen) # skip first line
        for line in fopen:
            line = line.strip()
            bart_result.append(dict(zip(bart_title, line.split('\t'))))
    return bart_result
            

if __name__ == '__main__':
    parse_bart_results('/Users/marvin/Projects/flask_playground/usercase/a_1534972940.637962/download/genelist1_bart_results.txt')