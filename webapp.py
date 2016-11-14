import os
from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
from prosupadm import ProSupADM

UPLOAD_FOLDER = '/home/pocs/Documents/usp/tcc/webapp/files'
IMAGES_FOLDER = '/home/pocs/Documents/usp/tcc/webapp/images'
ALLOWED_EXTENSIONS = set(['tsv'])

app = Flask(__name__, static_url_path="/images",
    static_folder="images")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "trabalho de tcc,dsf.usp"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'arquivotsv' not in request.files:
            flash('Nenhum arquivo presente.')
            return redirect(request.url)
        file = request.files['arquivotsv']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('Nenhum arquivo selecionado.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(
                datetime.now().strftime("%H%M%S%f") + file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
        else:
            flash("Arquivo com extensão incorreta. Envie um arquivo \
                TSV com os dados da captura como descrito no TCC.")

    return render_template('adm.html')

@app.route('/adm/<filename>')
def uploaded_file(filename):
    adm_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file = filename.rsplit('.', 1)[0] + ".jpg"

    if not os.path.exists(adm_file):
        flash("Resultado inexistente, envie seu arquivo novamente.")
        return redirect("/")

    psadm = ProSupADM()
    psadm.analyse(adm_file, url_for('static', filename=image_file)[1:])

    return render_template('resultado.html', image=image_file,
        admpronation=psadm.adm_pronation, admsupination=psadm.adm_supination,
        admtotal=psadm.adm_total)


if __name__ == "__main__":
    app.run()
