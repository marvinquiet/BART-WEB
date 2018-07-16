import os
import subprocess

PROJECT_DIR = os.path.dirname(__file__)
MARGE_DIR = os.path.join(PROJECT_DIR, "MARGE")
BAET_DIR = os.path.join(PROJECT_DIR, "BART")

# init marge env
def init_marge():
    # key = key_generator()
    key = "test" # key for one single user
    output_dir = os.path.join(PROJECT_DIR, "MARGE_"+key)
    create_dir(output_dir)
    
    cmd = "cd " + MARGE_DIR
    subprocess.Popen(cmd, shell=True)
    cmd = "marge init " + output_dir
    subprocess.Popen(cmd, shell=True)

    return output_dir


# edit config.json
def config_marge(output_dir):

    pass





def create_dir(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
