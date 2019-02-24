# -*- coding: utf-8 -*-
import os
import yaml
from flask import (Flask, flash, request, redirect, url_for, render_template, send_from_directory, session)
from werkzeug.utils import secure_filename

import do_process
import marge_bart
from utils import model_logger as logger

PROJECT_DIR = os.path.dirname(__file__)

# related to flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # submit job button
        if 'submit_button' in request.form:
            # fetch user name and generate unique project path
            username = request.form['username']
            jobname = request.form['jobname']
            user_key = do_process.generate_user_key(username, jobname)

            # docker user path
            user_path = do_process.init_project_path(user_key)

            # record user data
            user_data = {}
            user_data['user_email'] = username
            user_data['user_job'] = jobname
            user_data['user_key'] = user_key
            user_data['user_path'] = user_path
            user_data['dataType'] = request.form['dataType']
            user_data['assembly'] = request.form['species']
            user_data['files'] = []

            # process input data
            if user_data['dataType'] == "ChIP-seq":
                allowed_extensions = set(['bam', 'bed'])
                # execute bart only
                user_data['marge'] = False
                user_data['bart'] = True
            # process input data
            if user_data['dataType'] == "Geneset":
                allowed_extensions = set(['txt'])
                # execute marge+bart
                user_data['marge'] = True
                user_data['bart'] = True

                # if using genelist, save to file
                if request.form.get('uploadList', None):
                    gene_list = request.form['uploadList']
                    gene_list_file = 'genelist.txt'
                    gene_list_file_path = os.path.join(user_path, 'upload/' + gene_list_file)
                    with open(gene_list_file_path, 'w') as fopen:
                        for gene in gene_list:
                            fopen.write(gene)
                    user_data['files'].append(gene_list_file)

            if request.form['dataType'] == 'ChIP-seq' or \
                (request.form['dataType'] == 'Geneset' and request.form['geneType'] == 'geneFile'):	
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
                    # make sure the suffix of filename in [.txt, .bam, .bed] 	
                    if file and allowed_file(file.filename, allowed_extensions):	
                        filename = secure_filename(file.filename)	
                        upload_path = os.path.join(user_path, 'upload')	
                        filename_abs_path = os.path.join(upload_path, filename)	
                        file.save(filename_abs_path)	
                        user_data['files'].append(filename) # only save file name, since the uploaded path is always the same

            do_process.init_user_config(user_path, user_data)
            marge_bart.do_marge_bart(user_data)
            # post key 
            return redirect(url_for('show_key', key=user_key))

        # get result button
        if 'result_button' in request.form:
            user_key = request.form['result_button']
            # when key is null, refresh the website
            if user_key == "":
                return render_template('index.html')

            logger.info("Retrieve result: for " + user_key)

            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")

                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")

                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))
    return render_template('index.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

    return render_template('contact.html')

@app.route('/help', methods=['GET', 'POST'])
def help():
    if request.method == 'POST':
        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

    return render_template('help.html')

@app.route('/result', methods=['GET', 'POST'])
def get_result():
    if request.method == 'POST':
        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

    else:
        user_key = request.args['user_key']
        user_data = do_process.get_user_data(user_key)

        logger.info('Get result: for ' + user_key)
        logger.info(user_data)

        results = do_process.generate_results(user_data)
        results['sample'] = False
        return render_template('result_demonstration.html', results=results)

@app.route('/key', methods=['GET', 'POST'])
def show_key():
    user_key = request.args['key']
    if request.method == 'POST':
        if 'result_button' in request.form:
            user_key = request.form['result_button']
            # when key is null, refresh the website
            if user_key == "":
                return render_template('key_demonstration.html', key=request.args['key'])

            logger.info("Retrieve result: for " + user_key)
            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return render_template('key_demonstration.html', key=request.args['key'])

        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if do_process.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))
    
    return render_template('key_demonstration.html', key=user_key)

@app.route('/error', methods=['GET', 'POST'])
def error_page():
    err_msg = request.args['msg']
    return render_template('error.html', msg=err_msg)

@app.route('/plot/<userkey_tfname>')
def bart_plot_result(userkey_tfname):
    user_key, tf_name = userkey_tfname.split('___')
    # =========test d3.js below=============
    # use user_key to retrieve plot related results
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    bart_output_dir = os.path.join(user_path, 'download/bart_output')

    plot_results = do_process.generate_plot_results(bart_output_dir, tf_name)
    return render_template('plot_result.html', plotResults=plot_results)

    #============test end========================

    # where plots locate
    # plot_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key + '/download/bart_output/plot')
    # distribution_plot = '/download/bart_output/plot/' + user_key + '___' + tf_name + '_ranked_dot.png'
    # auc_plot = '/download/bart_output/plot/' + user_key + '___' + tf_name + '_cumulative_distribution.png'
    # plot_results = {}
    # plot_results['user_key'] = user_key
    # plot_results['tf_name'] = tf_name
    # plot_results['auc_plot'] = auc_plot
    # plot_results['dist_plot'] = distribution_plot
    # return render_template('plot_result.html', plotResults=plot_results)

@app.route('/log/<userkey_filename>')
def download_log_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    log_path = os.path.join(user_path, 'log')
    return send_from_directory(log_path, filename)

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

# @app.route('/download/bart_output/plot/<userkey_filename>')
# def download_bart_chart_file(userkey_filename):
#     user_key, filename = userkey_filename.split('___')
#     user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
#     download_path = os.path.join(user_path, 'download/bart_output/plot')
#     return send_from_directory(download_path, filename)


# ===== for genelist/ChIPdata sample =====

# download sample data
@app.route('/sample/<sample_type>')
def download_sample_file(sample_type):
    sample_path = ""
    sample_name = ""
    if sample_type == 'genelist':
        sample_name = "genelist.txt"
        sample_path = os.path.join(PROJECT_DIR, 'sample/genelist/upload')
    elif sample_type == 'ChIPdata':
        sample_name = "ChIPseq.txt"
        sample_path = os.path.join(PROJECT_DIR, 'sample/ChIPdata/upload')

    return send_from_directory(sample_path, sample_name)

# sample result
@app.route('/sample_result/<sample_type>')
def sample_result(sample_type):
    config_file = os.path.join(PROJECT_DIR, 'sample/' + sample_type + '/user.config')
    if not os.path.exists(config_file):
        return None

    user_data = {}
    with open(config_file, 'r') as fopen:
        user_data = yaml.load(fopen)

    if user_data:
        results = do_process.generate_results(user_data)
        if 'marge_result_files' in results:
            marge_result_list = []
            for marge_res_file in results['marge_result_files']:
                filename, file_url = marge_res_file
                marge_result_list.append((filename, file_url.replace('download', 'sample_download')))
            results['marge_result_files'] = marge_result_list

        if 'bart_result_files' in results:
            bart_result_list = []
            for bart_res_file in results['bart_result_files']:
                filename, file_url = bart_res_file
                bart_result_list.append((filename, file_url.replace('download', 'sample_download')))
            results['bart_result_files'] = bart_result_list

    results['sample'] = True
    results['sample_type'] = sample_type
    return render_template('result_demonstration.html', results=results)

# show sample plot result
@app.route('/sample_plot/<sample_type>/<tf_name>')
def bart_sample_plot_result(sample_type, tf_name):
    user_path = os.path.join(PROJECT_DIR, 'sample/' + sample_type)
    bart_output_dir = os.path.join(user_path, 'download/bart_output')

    plot_results = do_process.generate_plot_results(bart_output_dir, tf_name)
    return render_template('plot_result.html', plotResults=plot_results)

# download sample result files
@app.route('/sample_download/<userkey_filename>')
def download_sample_marge_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'sample/' + user_key)
    download_path = os.path.join(user_path, 'download')
    return send_from_directory(download_path, filename)

@app.route('/sample_download/bart_output/<userkey_filename>')
def download_sample_bart_res_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'sample/' + user_key)
    download_path = os.path.join(user_path, 'download/bart_output')
    return send_from_directory(download_path, filename)


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# if __name__ == '__main__':
#     app.run(debug=True,host='0.0.0.0')
