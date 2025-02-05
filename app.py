# import time
from functools import wraps
from time import time
import logging
import os
from parser.bri_llm import BRILargeLanguageModel

from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS

from parser.parser import process_files

app = Flask(__name__)

client = BRILargeLanguageModel(
    api_endpoint=os.getenv("LLAMA_ENDPOINT"),
    api_key=os.getenv("LLAMA_KEY")
)


# def async_timed(f):
#     @wraps(f)
#     async def wrapper(*args, **kwds):
#         start = time()
#         try:
#             result = await f(*args, **kwds)
#             elapsed = time() - start
#             logging.info(f"{f.__name__} took {elapsed:.4f} seconds to finish")
#             return result
#         except Exception as e:
#             elapsed = time() - start
#             logging.error(f"{f.__name__} failed after {elapsed:.4f} seconds")
#             raise

#     return wrapper


@app.route('/', methods=['GET', 'POST'])
# @async_timed
def get_response():
    if request.method != 'POST':
        return render_template('index.html')
    else:
        time_now = time()
        # try:
        files = request.files.getlist('resumes')

        if not files:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "URLs not provided"
                },
                "data": None,
            }), 400
        
        print("Parsing")
        
        # Start Parse
        responses = process_files(files, client, time_now)
        print(responses)
        # End Progress
        
        print("Parsing Complete")

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
        # except Exception as e:
        #     return jsonify({
        #         "status": {
        #             "code": 500,
        #             "message": str(e)
        #         },
        #         "data": None,
        #     }), 500

if __name__ == '__main__':
    app.run(debug=False)
