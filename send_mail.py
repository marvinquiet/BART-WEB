import os
import yaml

import utils
import do_process
from utils import model_logger as logger

PROJECT_DIR = os.path.dirname(__file__)

def send_mail():
    usercase_dir = os.path.join(PROJECT_DIR, 'usercase')
    for userkey in os.listdir(usercase_dir):
        user_path = os.path.join(usercase_dir, userkey)
        # iterate the user path
        if not os.path.isdir(user_path):
            continue
        
        user_data = do_process.get_user_data(userkey)
        if 'status' not in user_data: # not yet processing
            continue

        if 'user_email' in user_data:
            if user_data['user_email'] == '':
                continue

            if user_data['status'] == 'Done':
                logger.info('Send Email: send success e-mail to user {}'.format(userkey))
                send_flag, send_msg = utils.send_user_key(user_data['user_email'], userkey, user_data['status'])
                if send_flag:
                    logger.info('Send Email: ' + send_msg)
                else:
                    logger.error('Send Email: ' + send_msg)
                user_data['status'] = 'Sent'
                do_process.init_user_config(user_path, user_data)


            if user_data['status'] == 'Error':
                logger.info('Job Finish: send error e-mail to user {}'.format(userkey))
                send_flag, send_msg = utils.send_user_key(user_data['user_email'], userkey, user_data['status'])

                if send_flag:
                    logger.info('Send Email: ' + send_msg)
                else:
                    logger.error('Send Email: ' + send_msg)
                user_data['status'] = 'Sent'
                do_process.init_user_config(user_path, user_data)

send_mail()

