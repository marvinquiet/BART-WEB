# -*- coding: utf-8 -*-
import os
import json
from flask import (Flask, flash, request, redirect, url_for, render_template, send_from_directory, session)
from werkzeug.utils import secure_filename

import do_process
import marge_bart
from utils import model_logger as logger

PROJECT_DIR = os.path.dirname(__file__)
ALLOWED_EXTENSIONS = set(['txt', 'bam', '.bed'])

# related to flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # predict data button
        if request.form['index_submit'] == 'predict_data':
            return redirect(url_for('get_config'))
        # retrieve result button
        else:
            user_key = request.form['index_submit']

            # when key is null, refresh the website
            if user_key == "":
                return render_template('index.html')

            logger.info("retrieve result for " + user_key)

            if do_process.is_user_key_exists(user_key):
                logger.info("retrieve result: user exists.")

                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.info("retrieve result: did not find the result.")

                err_msg = "The key does not exist, make sure you enter the right key"
                return redirect(url_for('error_page', msg=err_msg))
    return render_template('index.html')


@app.route('/config-data', methods=['GET', 'POST'])
def get_config():
    if request.method == 'POST':
        # when "Predict your own data" button is clicked
        if request.form['start_prediction'] == 'start_prediction':
            # fetch user name and generate unique project path
            username = request.form['username']
            user_key = do_process.generate_user_key(username)
            # docker user path
            user_path = do_process.init_project_path(user_key)

            # record user data
            user_data = {}
            user_data['user_email'] = username
            user_data['user_key'] = user_key
            user_data['user_path'] = user_path
            user_data['dataType'] = request.form['dataType']
            user_data['assembly'] = request.form['assembly']
            # user_data['prediction_type'] = request.form.getlist('predictionType')
            user_data['files'] = []
        

            # remove 'gene_exp_type' and 'gene_id_type' from user_data
            # if user_data['dataType'] != "ChIP-seq":
            #     user_data['gene_exp_type'] = request.form['expTypeChoice']
            #     user_data['gene_id_type'] = request.form['geneIdChoice']
            # else:
            #     user_data['gene_exp_type'] = ""
            #     user_data['gene_id_type'] = ""
            

            # process what user has uploaded
            if 'uploadFiles' not in request.files:
                flash('Please choose a file')
                return redirect(request.url)
            files = request.files.getlist('uploadFiles')

            # if user does not select file, browser also
            # submit an empty part without filename
            for file in files:
                if file.filename == '':
                    flash('One of the files does not have a legal file name.')
                    return redirect(request.url)

                # make sure the suffix of filename in [.txt, .bam] 
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(user_path, 'upload')
                    filename_abs_path = os.path.join(upload_path, filename)
                    file.save(filename_abs_path)

                    user_data['files'].append(filename) # only save file name, since the uploaded path is always the same
            

            if user_data['dataType'] == "Geneset":
                user_data['marge'] = True
                user_data['bart'] = True
            else:
                user_data['marge'] = False
                user_data['bart'] = True

            # if u'tf' in user_data['prediction_type'] and \
            #     len(user_data['prediction_type']) == 1 and  \
            #     user_data['dataType'] == 'ChIP-seq':
            #     # only do bart profile with .bam file
            #     user_data['marge'] = False
            #     user_data['bart'] = True

            #     # marge_bart.exe_bart_profile(user_data)
            # elif u'tf' not in user_data['prediction_type']:
            #     # do marge process, repeat 3 times
            #     user_data['marge'] = True
            #     user_data['bart'] = False
            #     # marge_bart.do_marge_bart(user_key, False)
            # else:
            #     # do marge first to get enhancer prediction, and do bart geneset later
            #     user_data['marge'] = True
            #     user_data['bart'] = True

                # marge_bart.do_marge_bart(user_key, True)
            do_process.init_user_config(user_path, user_data)
            marge_bart.do_marge_bart(user_data)
            # post key 
            return redirect(url_for('show_key', key=user_key))
    return render_template('get_data_config.html')


@app.route('/result', methods=['GET', 'POST'])
def get_result():
    user_key = request.args['user_key']
    user_data = do_process.get_user_data(user_key)

    logger.info('get result for ' + user_key)
    logger.info(user_data)

    results = do_process.generate_results(user_data)
    return render_template('result_demonstration.html', results=results)


@app.route('/key')
def show_key():
    user_key = request.args['key']
    return render_template('key_demonstration.html', key=user_key)

@app.route('/error')
def error_page():
    err_msg = request.args['msg']
    return render_template('error.html', msg=err_msg)

@app.route('/plot/<userkey_tfname>')
def bart_plot_result(userkey_tfname):
    user_key, tf_name = userkey_tfname.split('___')
    # where plots locate
    # plot_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key + '/download/bart_output/plot')
    distribution_plot = '/download/bart_output/plot/' + user_key + '___' + tf_name + '_avg_z_p_boxplot.png'
    auc_plot = '/download/bart_output/plot/' + user_key + '___' + tf_name + '_cumulative_distribution.png'
    plot_results = {}
    plot_results['user_key'] = user_key
    plot_results['tf_name'] = tf_name
    plot_results['auc_plot'] = auc_plot
    plot_results['dist_plot'] = distribution_plot
    return render_template('plot_result.html', plotResults=plot_results)


@app.route('/download/<userkey_filename>')
def download_marge_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    download_path = os.path.join(user_path, 'download')
    return send_from_directory(download_path, filename)


@app.route('/download/bart_output/<userkey_filename>')
def download_bart_res_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    download_path = os.path.join(user_path, 'download/bart_output')
    return send_from_directory(download_path, filename)

@app.route('/download/bart_output/plot/<userkey_filename>')
def download_bart_chart_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    download_path = os.path.join(user_path, 'download/bart_output/plot')
    return send_from_directory(download_path, filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# if __name__ == '__main__':
#     app.run(debug=True,host='0.0.0.0')
