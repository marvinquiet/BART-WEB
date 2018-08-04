import os
import json
from flask import (Flask, flash, request, redirect, url_for, render_template, send_from_directory)
from werkzeug.utils import secure_filename

import do_process
import do_marge
import do_bart

PROJECT_DIR = os.path.dirname(__file__)
ALLOWED_EXTENSIONS = set(['txt', 'bam'])

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

            if do_process.is_user_key_exists(user_key):
                return redirect(url_for('get_result', user_key=user_key))
            else:
                msg = "User key does not exist, make sure you entered the right key"
                return render_template("error.html", msg=msg)
    return render_template('index.html')


@app.route('/config-data', methods=['GET', 'POST'])
def get_config():
    if request.method == 'POST':
        # when "Predict your own data" button is clicked
        if request.form['start_prediction'] == 'start_prediction':
            # fetch user name and generate unique project path
            username = request.form['username']
            user_key = do_process.generate_user_key(username)
            user_path = do_process.init_project_path(user_key)

            # record user data
            user_data = {}
            user_data['user_key'] = user_key
            user_data['user_path'] = user_path
            user_data['dataType'] = request.form['dataType']
            user_data['assembly'] = request.form['assembly']
            user_data['prediction_type'] = request.form.getlist('predictionType')
            if user_data['dataType'] != "ChIP-seq":
                user_data['gene_exp_type'] = request.form['expTypeChoice']
                user_data['gene_id_type'] = request.form['geneIdChoice']
            else:
                user_data['gene_exp_type'] = ""
                user_data['gene_id_type'] = ""
            user_data['files'] = []

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

                    user_data['files'].append(filename_abs_path)

            # 
            do_process.init_user_config(user_path, user_data)

            if u'tf' in user_data['prediction_type'] and \
                len(user_data['prediction_type']) == 1 and  \
                user_data['dataType'] == 'ChIP-seq':
                # only do bart profile with .bam file
                do_bart.exe_bart_profile(user_data)
                return render_template('key_demonstration.html', key=user_key)
            elif u'tf' not in user_data['prediction_type']:
                # init marge process
                if do_marge.init_marge(user_path):
                    do_marge.config_marge(user_data)
                    do_marge.exe_marge(user_path)
                else:
                    msg = "Init marge error! Please try again later!"
                    return render_template("error.html", msg=msg)
                return render_template('key_demonstration.html', key=user_key)
            else:
                # do marge first to get enhancer prediction, and do bart geneset later
                # init marge process
                if do_marge.init_marge(user_path):
                    do_marge.config_marge(user_data)
                    do_bart.exe_marge_and_bart(user_data)


                    # marge_proc = do_marge.exe_marge(user_path)
                    # do_bart.exe_bart_geneset(user_data, marge_proc)
                else:
                    msg = "Init marge error! Please try again later!"
                    return render_template("error.html", msg=msg)
                return render_template('key_demonstration.html', key=user_key)

            return render_template('key_demonstration.html', key=user_key)
    return render_template('get_data_config.html')


@app.route('/retrieve-result', methods=['GET', 'POST'])
def get_result():
    user_key = request.args['user_key']
    user_data = do_process.get_user_data(user_key)
    results = do_process.generate_results(user_data)


    return render_template('result_demonstration.html', results=results)


@app.route('/download/<userkey_filename>')
def download_log_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    download_path = os.path.join(user_path, 'download')
    return send_from_directory(download_path, filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


