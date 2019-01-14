# -*- coding: utf-8 -*-
import os
import json
import numpy as np
import pandas as pd
import scipy
from scipy import special
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

@app.route('/about', methods=['GET', 'POST'])
def about():
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

    return render_template('about.html')

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

# Irwin-Hall Distribution for plot
def factorial(n):
    value = 1.0
    while n>1:
        value*=n
        n-=1
    return value

def logfac(n):
    if n<20:
        return np.log(factorial(n))
    else:
        return n*np.log(n)-n+(np.log(n*(1+4*n*(1+2*n)))/6.0)+(np.log(np.pi))/2.0

def irwin_hall_cdf(x,n):
    # pval = returned_value for down regulated
    # pval = 1 - returned_value for up regulated
    value,k = 0,0
    while k<=np.floor(x):
        value +=(-1)**k*(special.binom(n,k))*(x-k)**n
        k+=1
    return value/(np.exp(logfac(n)))

@app.route('/plot/<userkey_tfname>')
def bart_plot_result(userkey_tfname):
    user_key, tf_name = userkey_tfname.split('___')
    # =========test d3.js below=============
    # use user_key to retrieve plot related results
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    bart_output_dir = os.path.join(user_path, 'download/bart_output')

    # _auc.txt and _bart_result.txt files
    bart_auc_ext = '_auc.txt'
    bart_res_ext = '_bart_results.txt'

    AUCs = {}
    tfs = {}
    bart_df = {}
    bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank']
    for root, dirs, files in os.walk(bart_output_dir):
        for bart_file in files:
            if bart_res_ext in bart_file:
                bart_result_file = os.path.join(root, bart_file)
                bart_df = pd.read_csv(bart_result_file, sep='\t', names=bart_title[1:], index_col=0, skiprows=1)
            if bart_auc_ext in bart_file:
                bart_auc_file = os.path.join(root, bart_file)
                with open(bart_auc_file, 'r') as fopen:
                    for line in fopen:
                        tf_key, auc_equation = line.strip().split('\t')
                        auc = float(auc_equation.replace(' ', '').split('=')[1])
                        AUCs[tf_key] = auc

                for tf_key in AUCs.keys():
                    tf = tf_key.split('_')[0]
                    auc = AUCs[tf_key]
                    if tf not in tfs:
                        tfs[tf] = [auc]
                    else:
                        tfs[tf].append(auc)
    plot_results = {}
    plot_results['tf_name'] = tf_name

    # generate cumulative data
    cumulative_data = {}
    background = []
    for tf in tfs:
        background.extend(tfs[tf])
    target = tfs[tf_name]
    background = sorted(background)
    dx = 0.01
    x = np.arange(0,1,dx)
    by,ty = [],[]
    for xi in x:
        by.append(sum(i< xi for i in background )/len(background))
        ty.append(sum(i< xi for i in target )/len(target))

    cumulative_data['x'] = list(x)
    cumulative_data['bgY'] = by
    cumulative_data['tfY'] = ty
    cumulative_data = [dict(zip(cumulative_data,t)) for t in zip(*cumulative_data.values())]
    plot_results['cumulative_data'] = cumulative_data

    # rankdot data
    rankdot_data = []
    rankdot_pair = {}
    col = 'r_rank'
    for tf_id in bart_df.index:
        rankdot_pair['rank_x'] = list(bart_df.index).index(tf_id)+1
        rankdot_pair['rank_y'] = -1*np.log10(irwin_hall_cdf(3*bart_df.loc[tf_id][col],3))
        rankdot_data.append(rankdot_pair)
        rankdot_pair = {}
    plot_results['rankdot_data'] = rankdot_data

    rankdot_pair['rank_x'] = list(bart_df.index).index(tf_name)+1
    rankdot_pair['rank_y'] = -1*np.log10(irwin_hall_cdf(3*bart_df.loc[tf_name][col],3))
    plot_results['rankdot_TF'] = [rankdot_pair]

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

@app.route('/download/bart_output/plot/<userkey_filename>')
def download_bart_chart_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    download_path = os.path.join(user_path, 'download/bart_output/plot')
    return send_from_directory(download_path, filename)


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# if __name__ == '__main__':
#     app.run(debug=True,host='0.0.0.0')
