from flask import Flask, request, send_file, render_template, redirect, url_for, jsonify
from translator import PptxTranslator
import os
import pathlib
import threading
from threading import Lock

progress_lock = Lock()
progress = 0            

exporting_threads = {}
app = Flask(__name__)
app.debug = True
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Ensure upload and output folders exist
pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
pathlib.Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


class TranslatorThread(threading.Thread):
    def __init__(self, src_lang, tgt_lang, orig_file_path, translated_file_path, ignore_terms):
        threading.Thread.__init__(self)
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.orig_file_path = orig_file_path
        self.translated_file_path = translated_file_path
        self.ignore_terms = ignore_terms

    def run(self):
        global progress
        def update_progress(value):
            global progress
            with progress_lock: 
                progress = value
        translator = PptxTranslator(self.src_lang, self.tgt_lang, ignore_terms=self.ignore_terms)
        translator.translate_presentation(self.orig_file_path, self.translated_file_path, progress_callback=update_progress)
        with progress_lock: 
            progress = 100


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    global progress
    progress = 0 
    src_lang = request.form['src_lang']
    tgt_lang = request.form['tgt_lang']
    
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"

    ignore_terms = []
    if 'ignore_terms' in request.files:
        ignore_terms_file = request.files['ignore_terms']
        if ignore_terms_file and ignore_terms_file.filename != '':
            ignore_terms_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ignore_terms_file.filename)
            ignore_terms_file.save(ignore_terms_file_path)
            
            # Read ignore terms from the uploaded file
            with open(ignore_terms_file_path, 'r') as f:
                ignore_terms = [line.strip() for line in f.readlines() if line.strip()]

    if file:
        orig_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(orig_file_path)
        
        translated_file_path = os.path.join(app.config['OUTPUT_FOLDER'], f'translated_{file.filename}')

        translator_thread = TranslatorThread(src_lang, tgt_lang, orig_file_path, translated_file_path, ignore_terms)
        translator_thread.start()
        
        return send_file(translated_file_path, as_attachment=True)
        # return jsonify({"message": "Translation started"})

@app.route('/progress', methods=['GET'])
def get_progress():
    global progress
    with progress_lock:  # Use lock to safely read progress
        current_progress = progress
    return jsonify({"progress": current_progress})

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
    