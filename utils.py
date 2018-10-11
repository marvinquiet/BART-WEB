# -*- coding: utf-8 -*-

import os
import shutil

def create_dir(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            shutil.rmtree(directory)
            os.makedirs(directory)

    except OSError:
        print ('Error: Creating directory. ' +  directory)

def get_files_in_dir(proc_type, directory):
    sample_files = ""
    for content in os.listdir(directory):
        if proc_type == "ChIP" and ".bam" in content:
            sample_files += content[:-4] + ' '
        elif proc_type == "GeneList" and ".txt" in content:
            sample_files += content[:-4] + ' '
    return sample_files.strip()