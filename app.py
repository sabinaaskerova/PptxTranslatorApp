from flask import Flask, request, send_file, render_template, jsonify, after_this_request
from translator import PptxTranslator
import os
import pathlib
import threading
from threading import Lock

progress_lock = Lock()  
progress = 0           
translation_done = False  
translation_thread = None

app = Flask(__name__)
app.debug = True
UPLOAD_FOLDER = os.path.abspath('uploads')
OUTPUT_FOLDER = os.path.abspath('outputs')

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
        global translation_done

        def update_progress(value):
            global progress
            with progress_lock:
                progress = value  # Update the global progress safely
        try:
            # Initialize the translator and start the translation process
            translator = PptxTranslator(self.src_lang, self.tgt_lang, ignore_terms=self.ignore_terms)
            translator.translate_presentation(self.orig_file_path, self.translated_file_path, progress_callback=update_progress)
            
            with progress_lock:
                progress = 100  # Set progress to 100% when done
        except FileNotFoundError as e:
            print(f"Error: {e}") 
        finally:
            translation_done = True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/translate', methods=['POST'])
def translate():
    global progress
    global translation_done
    global translation_thread

    progress = 0  # Reset progress at the start
    translation_done = False  # Reset translation state

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

        if not os.path.exists(orig_file_path):
            return jsonify({"error": "File could not be saved"}), 500

        translated_file_path = os.path.join(app.config['OUTPUT_FOLDER'], f'translated_{file.filename}')

        translation_thread = TranslatorThread(src_lang, tgt_lang, orig_file_path, translated_file_path, ignore_terms)
        translation_thread.start()

        # Return a success response so the frontend can start polling progress
        return jsonify({"message": "Translation started"})


@app.route('/progress', methods=['GET'])
def get_progress():
    global progress
    with progress_lock:
        current_progress = progress
    return jsonify({"progress": current_progress})


@app.route('/check_completion', methods=['GET'])
def check_completion():
    global translation_done
    if translation_done:
        return jsonify({"done": True})
    return jsonify({"done": False})


@app.route('/download/<filename>')
def download(filename):
    translated_file_path = os.path.join(app.config['OUTPUT_FOLDER'], f'translated_{filename}')
    original_file_pah = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}')

    if not os.path.exists(translated_file_path):
        return jsonify({"error": "File not found"}), 404

    @after_this_request
    def remove_file(response):
        try:
            os.remove(translated_file_path)
            os.remove(original_file_pah)
        except Exception as e:
            print(f"Error deleting files")
        return response

    return send_file(translated_file_path, as_attachment=True)

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
