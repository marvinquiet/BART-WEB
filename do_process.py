import os
import subprocess
import shutil
import json

PROJECT_DIR = os.path.dirname(__file__)
MARGE_DIR = os.path.join(PROJECT_DIR, "MARGE")
BAET_DIR = os.path.join(PROJECT_DIR, "BART")
UPLOADED_DIR = os.path.join(PROJECT_DIR, "uploads")

# init marge env
def init_marge():
    # key = key_generator()
    key = "test" # key for one single user
    marge_output_dir = os.path.join(PROJECT_DIR, "MARGE_"+key)
    marge_input_dir = os.path.join(marge_output_dir, "input")
    create_dir(marge_output_dir)
    create_dir(marge_input_dir)

    # copy uploaded files into marge_output directory
    src_files = os.listdir(UPLOADED_DIR)
    for file_name in src_files:
        full_file_name = os.path.join(UPLOADED_DIR, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, marge_input_dir)

    # subprocess.call(["cd", MARGE_DIR])
    marge_res = subprocess.check_call(["marge", "init", marge_output_dir])
    if marge_res == 0:
        return True, [marge_output_dir, marge_input_dir]
    else:
        return False,


# edit config.json
def config_marge(marge_output_dir, marge_input_dir):
    config_file = os.path.join(marge_output_dir, 'config.json')
    config_file_bak = os.path.join(marge_output_dir, 'config.json.bak')

    shutil.copyfile(config_file, config_file_bak)

    with open(config_file) as data_file:
        data = json.load(data_file)

    data["tools"]["MACS2"] = "/usr/local/Cellar/pyenv/1.2.1/versions/venv2.7/bin/macs2"

    marge_tools_dir = os.path.join(MARGE_DIR, "marge_ucsc_tools")
    data["tools"]["bedClip"] = os.path.join(marge_tools_dir, "bedClip")
    data["tools"]["bedGraphToBigWig"] = os.path.join(marge_tools_dir, "bedGraphToBigWig")
    data["tools"]["bigWigAverageOverBed"] = os.path.join(marge_tools_dir, "bigWigAverageOverBed")
    data["tools"]["bigWigSummary"] = os.path.join(marge_tools_dir, "bigWigSummary")

    data["ASSEMBLY"] = "hg38"
    data["MARGEdir"] = os.path.join(MARGE_DIR, "marge")
    marge_ref_dir = os.path.join(MARGE_DIR, "marge_ref")
    data["REFdir"] = os.path.join(marge_ref_dir, data["ASSEMBLY"] + "_all_reference")

    proc_type = "ChIP"
    if proc_type == "ChIP":
        data["EXPSDIR"] = ""
        data["EXPS"] = ""
        data["EXPTYPE"] = ""
        data["ID"] = ""
        data["SAMPLESDIR"] = marge_input_dir
        data["SAMPLES"] = get_files_in_dir("ChIP", data["SAMPLESDIR"])
    elif proc_type == "GeneList":
        data["SAMPLESDIR"] = ""
        data["SAMPLES"] = ""
        data["EXPSDIR"] = marge_input_dir
        data["EXPS"] = get_files_in_dir("GeneList", data["EXPSDIR"])
        data["EXPTYPE"] = "Gene_Only"  # Gene_Only & Gene_Response
        data["ID"] = "GeneSymbol" # GeneSymbol & RefSeq
    elif proc_type == "Both":
        data["SAMPLESDIR"] = marge_input_dir
        data["EXPSDIR"] = marge_input_dir
        data["SAMPLES"] = get_files_in_dir("ChIP", data["SAMPLESDIR"])
        data["EXPS"] = get_files_in_dir("GeneList", data["EXPSDIR"])
        data["EXPTYPE"] = "Gene_Only"  # Gene_Only & Gene_Response
        data["ID"] = "GeneSymbol" # GeneSymbol & RefSeq

    with open(config_file, 'w') as data_file:
        json.dump(data, data_file)


def exe_marge(marge_output_dir):
    # print (subprocess.check_call(["cd", marge_output_dir]))
    # print (marge_output_dir)
    # cmd = "cd %s && snakemake -n" % (marge_output_dir)
    # os.system(cmd)
    res = subprocess.Popen(["snakemake", "-n"], stdout=subprocess.PIPE, cwd=marge_output_dir).communicate()
    print (res[0])
    with open(os.path.join(marge_output_dir, 'snakemake_res.txt'), 'wb') as f_snake_res:
        f_snake_res.write(res[0])
    res = subprocess.Popen(["snakemake", "--cores", "1"], cwd=marge_output_dir).communicate()
    print (res[0])



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
