# -*- coding: utf-8 -*-

import os
import shutil
import logging
import boto3
# for sending key to user
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from logging.handlers import RotatingFileHandler

PROJECT_DIR = os.path.dirname(__file__)

def create_dir(directory):
    try:
        if not os.path.exists(directory):
            oldmask = os.umask(000)
            os.makedirs(directory,0777)
            os.umask(oldmask)
        else:
            shutil.rmtree(directory)
            oldmask = os.umask(000)
            os.makedirs(directory,0777)
            os.umask(oldmask)

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
    queue_info = os.path.join(PROJECT_DIR, 'usercase/queue_info.txt')
    with open(queue_info) as f1:
        ID = f1.read().splitlines()
    sqs = boto3.resource('sqs', region_name='us-east-1',aws_access_key_id=ID[0],aws_secret_access_key =ID[1])
    queue = sqs.get_queue_by_name(QueueName='BARTweb1')
    response = queue.send_message(MessageBody='BART submission', MessageAttributes={
        'submissionkey': {
            'StringValue': directory,
            'DataType': 'String'
        }
    })


# send user key to user e-mail
def send_user_key(user_mail, user_key, email_type):
    MY_ADDRESS = "zanglab.service@gmail.com"
    PASSWORD = "ZangLab2018"

    msg = MIMEMultipart()
    msg['From'] = MY_ADDRESS
    msg['To'] = user_mail

    if email_type == 'Submit':
        msg['Subject'] = "BART key"
        # better change to a file template later
        message = '''
Hi there,

Thank you for using BART web!

Here is your key: {}

When the job is done, you can ge the results through this link: {}
'''.format(user_key, 'http://bartweb.org/result?user_key='+user_key)
    elif email_type == 'Done':
        msg['Subject'] = "BART result"
        message = '''
Congratulations! Your BART job is done!

Please get the results through this link: {}
'''.format('http://bartweb.org/result?user_key='+user_key)
    elif email_type == 'Error':
        msg['Subject'] = "BART error"
        message = '''
Unfortunately, your BART job ends with errors.

Please check whether you chose the correct species or uploaded the required format file.

Or reach us at wm9tr@virginia.edu with your key: {}

'''.format(user_key)
    else:
        pass

    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP_SSL("smtp.gmail.com")
    try:
        server.login(MY_ADDRESS, PASSWORD)
        msg = msg.as_string()
        server.sendmail(MY_ADDRESS, user_mail, msg)
    except smtplib.SMTPAuthenticationError:
        return False, "username of password is wrong"
    except:
        return False, "errors in sending key to e-mail..."
    finally:
        server.quit()  # finally close the connection with server

    return True, "send e-mail to user successfully..."


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
