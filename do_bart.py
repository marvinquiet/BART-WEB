# import os
# import subprocess
# import json
# import shutil

# import utils

# PROJECT_DIR = os.path.dirname(__file__)
# BART_DIR = os.path.join(PROJECT_DIR, "BART")

# BART_CORE = 1

# def exe_bart_profile(user_data):
#     '''
#     Usage:
#     bart profile [-h] <-i infile> <-f format> <-s species> [-t target] [-p processes] [--outdir] [options]

#     Example:

#     bart profile -i ChIP.bed -f bed -s hg38 -t target.txt -p 4 --outdir bart_output
#     '''
#     bart_output_path = os.path.join(user_data['user_path'], 'download')
#     target_file_path = os.path.join(BART_DIR, 'BART/{assembly_type}_library/{assembly_type}_test_data/target.txt'.format(assembly_type=user_data["assembly"]))

#     for input_file in user_data['files']:
#         if input_file.endswith(".bam"):
#             subprocess.Popen(["bart", "profile", "-i", input_file, "-f", "bam", "-s", user_data["assembly"], "-t", target_file_path, "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)


# def exe_bart_geneset(user_data):
#     '''
#     Usage:
#     bart geneset [-h] <-i infile> <-s species> [-t target] [-p processes] [--outdir] [options]

#     Example:

#     bart geneset -i name_enhancer_prediction.txt -s hg38 -t target.txt -p 4 --outdir bart_output
#     '''
#     bart_output_path = os.path.join(user_data['user_path'], 'download')
#     target_file_path = os.path.join(BART_DIR, 'BART/{assembly_type}_library/{assembly_type}_test_data/target.txt'.format(assembly_type=user_data["assembly"]))
    
#     eh_files = get_enhancer_prediction(user_data['user_path'])
#     for eh_file in eh_files:
#         subprocess.Popen(["bart", "geneset", "-i", eh_file, "-s", user_data["assembly"], "-t", target_file_path, "-p", str(BART_CORE), "--outdir", bart_output_path], cwd=bart_output_path)


# def get_enhancer_prediction(user_path):
#     # marge output file path
#     eh_files = []
#     eh_files_path = os.path.join(user_path, 'marge_data/margeoutput/cisRegions')
#     for eh_file in os.listdir(eh_files_path):
#         if '_enhancer_prediction.txt' in str(eh_file):
#             eh_files.append(os.path.join(eh_files_path, eh_file))

#     return eh_files