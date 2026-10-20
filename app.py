import logging
from time import time

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from parser.llm_clients import build_client_from_env
from parser.parser import process_files

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB per request
client = build_client_from_env()


@app.route('/', methods=['GET', 'POST'])
def get_response():
    if request.method != 'POST':
        return render_template('index.html')
    else:
        time_now = time()
        files = request.files.getlist('resumes')

        if not files:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "No files uploaded (form field 'resumes')"
                },
                "data": None,
            }), 400
        
        responses = process_files(files, client, time_now)

        if all(response['cv'] is not None for response in responses):
            return jsonify({
                "status": {
                    "code": 200,
                    "message": "All files parsed successfully!"
                },
                "data": responses,
            }), 200
        else:
            return jsonify({
                "status": {
                    "code": 206,
                    "message": "Partial or none of files parsed successfully! Some or all files failed."
                },
                "data": responses,
            }), 206


if __name__ == '__main__':
    app.run(debug=False)
