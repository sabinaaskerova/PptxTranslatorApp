from flask import Flask, request, send_file, render_template, redirect, url_for
from translator import PptxTranslator
import os
import pathlib

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Ensure upload and output folders exist
pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
pathlib.Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    src_lang = request.form['src_lang']
    tgt_lang = request.form['tgt_lang']
    
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    if file:
        orig_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(orig_file_path)
        
        translated_file_path = os.path.join(app.config['OUTPUT_FOLDER'], f'translated_{file.filename}')
        
        translator = PptxTranslator(src_lang, tgt_lang)
        translator.translate_presentation(orig_file_path, translated_file_path)
        
        return send_file(translated_file_path, as_attachment=True)

@app.teardown_request
def teardown_cleanup(exception=None): #ensures that files are cleaned up even if an exception occurs during request processing.
    try:
        for filename in os.listdir(app.config['OUTPUT_FOLDER']):
            file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error during teardown cleanup: {e}")

if __name__ == '__main__':
    app.run(debug=True)
    