import os
from flask import (Flask, flash, request, redirect, url_for, render_template)
from werkzeug.utils import secure_filename
from flask import send_from_directory

import do_process
import do_marge

PROJECT_DIR = os.path.dirname(__file__)
ALLOWED_EXTENSIONS = set(['txt', 'bam'])

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form['index_submit'] == 'predict_data':
            return redirect(url_for('test_getting_config'))
        else:
            user_key = request.form['index_submit']
            if do_process.is_user_key_exists(user_key):
                return redirect(url_for('test_getting_result', user_key=user_key))
            else:
                msg = "User key does not exist, make sure you entered the right user_key"
                return render_template("error.html", msg=msg)
    return render_template('index.html')


@app.route('/config-data', methods=['GET', 'POST'])
def test_getting_config():
    if request.method == 'POST':
        if request.form['start_prediction'] == 'start_prediction':
            username = request.form['username']
            user_key = do_process.generate_user_key(username)
            user_path = do_process.init_project_path(user_key)

            # record user data
            user_data = {}
            user_data['user_path'] = user_path
            user_data['dataType'] = request.form['dataType']
            user_data['assembly'] = request.form['assembly']
            user_data['prediction_type'] = request.form.getlist('predictionType')
            user_data['gene_exp_type'] = request.form['expTypeChoice']
            user_data['gene_id_type'] = request.form['geneIdChoice']
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

                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(user_path, 'upload')
                    filename_abs_path = os.path.join(upload_path, filename)
                    file.save(filename_abs_path)

                    user_data['files'].append(filename_abs_path)

            do_process.init_user_config(user_path, user_data)


            # what marge should do
            if u'rp' in user_data['prediction_type'] or u'cis' in user_data['prediction_type'] or u'eh' in user_data['prediction_type']:
                # init marge process
                if do_marge.init_marge(user_path):
                    do_marge.config_marge(user_path, user_data)
                    do_marge.exe_marge(user_path)
                else:
                    msg = "Init marge error! Please try again later!"
                    return render_template("error.html", msg=msg)

            # what bart should do
            if u'tf' in user_data['prediction_type']:
                pass

            return render_template('key_demonstration.html', key=user_key)
    return render_template('get_data_config.html')


@app.route('/retrieve-result', methods=['GET', 'POST'])
def test_getting_result():
    user_key = request.args['user_key']
    user_data = do_process.get_user_data(user_key)
    results = do_process.generate_results(user_data)

    return render_template('result_demonstration.html', results=results)

    # if do_marge.is_marge_done(user_data['user_path']):
    #     return render_template('result_demonstration.html', result=result)
    # else:
    #     return render_template('result_demonstration.html', result=result)
        

    


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


