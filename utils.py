# -*- coding: utf-8 -*-

import os
import shutil
import logging
import boto3
from logging.handlers import RotatingFileHandler


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

def send_sqs_message(directory):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='bart-web')
    response = queue.send_message(MessageBody='BART submission', MessageAttributes={
        'submission': {
            'StringValue': directory,
            'DataType': 'String'
        }
    })

################################
# Conf to edit
################################
DebugConf = True
#DebugConf = False


################################
# Init Loggers
################################
model_logger = logging.getLogger('bart-web')


################################
# Init Handlers
################################
formatter = logging.Formatter('[%(asctime)s][pid:%(process)s-tid:%(thread)s] %(module)s.%(funcName)s: %(levelname)s: %(message)s')

# StreamHandler for print log to console
hdr = logging.StreamHandler()
hdr.setFormatter(formatter)
hdr.setLevel(logging.DEBUG)

# RotatingFileHandler
## Set log dir
abs_path = os.path.dirname(os.path.abspath(__file__))
log_dir_path = abs_path + '/log'
if not os.path.exists(log_dir_path):
    os.makedirs(log_dir_path)

## Specific file handler
fhr_model = RotatingFileHandler('%s/bart-web.log'%(log_dir_path), maxBytes=10*1024*1024, backupCount=3)
fhr_model.setFormatter(formatter)
fhr_model.setLevel(logging.DEBUG)


################################
# Add Handlers
################################
model_logger.addHandler(fhr_model)
if DebugConf:
    model_logger.addHandler(hdr)
    model_logger.setLevel(logging.DEBUG)
else:
    model_logger.setLevel(logging.ERROR)


if __name__ == '__main__':
    '''
    Usage:
    from tools.log_tools import data_process_logger as logger
    logger.debug('debug debug')
    '''
    model_logger.info('Ohhh model')
    model_logger.error('error model')
