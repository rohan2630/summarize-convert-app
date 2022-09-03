# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 15:01:08 2022

@author: Rohan Mathur
"""

from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from transformers import pipeline

import os

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_EXTENSIONS'] = ['.pdf', '.mp3' ]
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024
app.config['SECRET_KEY'] = "supersecretkey"

ALLOWED_EXTENSIONS = set(['pdf', 'mp3'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summaryInput')
def summaryInput():
    return render_template('summaryInput.html')

@app.route('/summaryInput', methods=['POST'])
def summaryUpload():
    my_files = request.files    
    session['start'] = int(request.form.get('start'))
    session['end'] = int(request.form.get('end'))
    session['choice'] = int(request.form.get('choice'))
    miscellaneous = ['header', 'myText']
    misc = []

    for item in my_files:
        uploaded_file = my_files.get(item)
        uploaded_file.filename = secure_filename(uploaded_file.filename)
    pdfFiles = [val for sublist in [[os.path.join(i[0], j) for j in i[2] if j.endswith('.pdf')] for i in os.walk('./')] for val in sublist]
    for i in pdfFiles:
        os.remove(i)
    uploaded_file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(uploaded_file.filename)))
        
    f = request.form
    for key in f.keys():
        if key in miscellaneous:
            for value in f.getlist(key):
                misc.append(value)
                
    for i in range(len(misc)):
        session[i] = misc[i]

    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    text = "Uploaded"
    misc = []
    pdfFiles = [val for sublist in [[os.path.join(i[0], j) for j in i[2] if j.endswith('.pdf')] for i in os.walk('./')] for val in sublist]
    for i in pdfFiles:
        reader = PdfReader(i)
        
    start = session.get('start')
    end = session.get('end')
    choice = session.get('choice')
    for i in range(10):
        if session.get(i):
            misc.append(session.get(i))
    
    new_str = ""
    
    for i in range(start-1, end):
        new_str += reader.pages[i].extract_text()
        
    new_str = new_str.replace("\n", "")
    new_str = new_str.replace("\t", "")
        
    if choice != 1:
        if choice == 2:
            for i in range(1, end + 1):
                new_str = new_str.replace(f"{i}", "")
        elif choice == 3:
            for i in range(1, end + 1):
                new_str = new_str.replace(f"Page {i}", "")
        elif choice == 4:
            for i in range(1, end + 1):
                new_str = new_str.replace(f"Page {i} of ", "")
                
    for i in misc:
        new_str = new_str.replace(i, "")
    
    with open("static/files/new_str.txt", 'w') as new:
        new.write(new_str)
        
    max_chunk = 500
    new_str = new_str.replace(".", ".<eos>")
    new_str = new_str.replace("?", "?<eos>")
    new_str = new_str.replace("!", "!<eos>")
    
    sentences = new_str.split('<eos>')
    current_chunk = 0
    chunks = []
    for sentence in sentences:
        if len(chunks) == current_chunk + 1:
            if len(chunks[current_chunk]) + len(sentence.split(" ")) <= max_chunk:
                chunks[current_chunk].extend(sentence.split(" "))
            else:
                current_chunk += 1
                chunks.append(sentence.split(" "))
        else:
            chunks.append(sentence.split(" "))
    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = " ".join(chunks[chunk_id])
        
    with open('static/files/new_str1.txt', 'w') as new_str1:
        new_str1.write("Reached")
        
    summarizer = pipeline("summarization", model="t5-base", tokenizer="t5-base", framework="tf")
    res = summarizer(chunks, max_length=290, min_length=30, do_sample=False)
    
    text = ' '.join([summ['summary_text'] for summ in res])
    text = text.split('.')
    for i in range(len(text)):
        text[i] = text[i].strip().capitalize()
    text = '.\n\n--> '.join(text)
    i = len(text)-1
    while text[i] != '.':
        text = text.rstrip(text[-1])
        i = len(text)-1
    text = '--> ' + text
        
    with open("static/files/summary.txt", "w") as f:
        f.write(text)
    return render_template('summary.html', text=text)


@app.route('/audioInput')
def audioInput():
    return render_template('audioInput.html')

@app.route('/audio')
def audio():
    return render_template('audio.html')


if __name__ == "__main__":
    app.run(debug=True)