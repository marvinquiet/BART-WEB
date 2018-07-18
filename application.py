import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from flask import send_from_directory

import do_process

PROJECT_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
ALLOWED_EXTENSIONS = set(['txt', 'bam'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename_abs_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filename_abs_path)

            marge_res = do_process.init_marge()
            if marge_res[0]:
                # do marge process
                do_process.config_marge(marge_res[1][0], marge_res[1][1])
                do_process.exe_marge(marge_res[1][0])
                return "File uploaded succeed! Marge init succeed!"
            else:
                return "File uploaded succeed! Marge init failed!"

    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
