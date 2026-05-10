import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from pypdf import PdfReader
from gtts import gTTS

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# ---------- BASIC "AI" STUB (you can upgrade later) ----------

def generate_from_notes(notes, mode):
    notes = notes.strip()
    if not notes:
        return {"error": "No notes provided."}

    if mode == "flashcards":
        # super simple demo logic
        lines = [l.strip() for l in notes.split("\n") if l.strip()]
        cards = []
        for i, line in enumerate(lines[:10], start=1):
            cards.append({
                "front": f"Key idea {i}",
                "back": line
            })
        return {"type": "flashcards", "cards": cards}

    if mode == "mcq":
        return {
            "type": "mcq",
            "questions": [
                {
                    "question": "What is one key idea from your notes?",
                    "options": ["Idea A", "Idea B", "Idea C", "Idea D"],
                    "answer": "Idea A"
                }
            ]
        }

    if mode == "exam":
        return {
            "type": "exam",
            "questions": [
                {
                    "question": "Explain one of the main concepts from your notes.",
                    "marks": 4
                }
            ]
        }

    if mode == "podcast":
        script = (
            "Welcome to your personal study podcast. "
            "Today we’ll review the key ideas from your notes. "
            f"Here is a summary: {notes[:600]} ..."
        )
        return {"type": "podcast", "script": script}

    return {"error": "Unknown mode."}

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        text = ""
        if file.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(filepath)

        return jsonify({
            'message': 'File uploaded successfully!',
            'filename': file.filename,
            'text': text
        })

    return jsonify({'error': 'File type not allowed (only PDF for now).'}), 400

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    notes = data.get("notes", "")
    mode = data.get("mode", "flashcards")

    result = generate_from_notes(notes, mode)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/podcast-audio', methods=['POST'])
def podcast_audio():
    data = request.get_json()
    script = data.get('script', '')
    if not script:
        return jsonify({'error': 'No script provided'}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    tts = gTTS(script)
    tts.save(path)

    return jsonify({'audio_url': f'/audio/{filename}'})

@app.route('/audio/<name>')
def audio(name):
    path = os.path.join(app.config['UPLOAD_FOLDER'], name)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(debug=True)
