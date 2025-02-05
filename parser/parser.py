import asyncio
import json
import time
import os
from functools import wraps
from time import time
import logging

from parser.bri_llm import BRILargeLanguageModel
from parser.document import read_docx, read_pdf
from dotenv import load_dotenv

load_dotenv()

def read_file_content(file):
    # try:
    file_name = file.filename
    file_extension = file_name.split('.')[-1].lower()

    if file_extension == 'pdf':
        return read_pdf(file)
    elif file_extension in ['doc', 'docx']:
        return read_docx(file)
    else:
        raise Exception("Extension denied!")
    # except Exception as e:
    #     raise Exception(str(e))

# logging.basicConfig(
#     filename="timing.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )

# def async_timed(f):
#     @wraps(f)
#     async def wrapper(*args, **kwds):
#         start = time()
#         # try:
#         result = await f(*args, **kwds)
#         elapsed = time() - start
#         logging.info(f"{f.__name__} took {elapsed:.4f} seconds to finish")
#         return result
#         # except Exception as e:
#         elapsed = time() - start
#         logging.error(f"{f.__name__} failed after {elapsed:.4f} seconds")
#         raise

#     return wrapper

def read_prompt():
    """Function to read prompt.txt content"""
    # try:
    with open("prompt.txt", "r") as file:
        return file.read().strip()
    # except Exception as e:
    raise Exception(f"Failed to read prompt.txt: {str(e)}")

# @async_timed
def parse_file(file, client, time_now):

    print(f"Parse [1/7]: Parsing File...")
    # try:
    print(f"Parse [2/7]: Make Context...")
    context = f"CV\n{read_file_content(file)}\n\n"

    print(f"Parse [3/7]: Make Prompt...")
    prompt = read_prompt()  # Load the prompt from prompt.txt

    print(f"Parse [4/7]: Hit LLM API...")
    
    # Define messages and sampling parameters
    messages = [
        {
            "role": "system",
            "content": "You are CV Parsing master"
        },
        {
            "role": "user",
            "content": f"{prompt}",
        },
        {
            "role": "user",
            "content": f"{context}" 
        }
    ]

    print(messages)
    
    sampling_params = {
        "temperature": 0.0,
        "top_p": 0.95,
        "max_tokens": 9216  # Increased token limit for PDF resumes
    }
    
    # Obtain response from LLM
    response = client.create_response(
        messages=messages,
        sampling_params=sampling_params
    )

    print(f"Parse [5/7]: Obtain Response...")

    # print(response)

    # Extract LLM response
    if not response["function_call"]:
        response = response["llm_answer"].replace("\n", "")
        response = response.strip("[]")
        print(response)
        response_json = json.loads(response)
    else:
        response_json = response["function_call"][0]
    print(json.dumps(response_json, indent=4))

    # print(f"Parse [6/7]: Converting to JSON...")

    # print(llm_answer)
    # # Convert response to JSON
    # response_json = json.loads(llm_answer)
    print(f"Parse [7/7]: Finish parsing a file with time: ", time() - time_now)

    return {
        "cv": response_json,
        "status": {
            "code": 200,
            "message": "CV parsed successfully."
        }
    }
    # except Exception as e:
    print(f"Error parsing file: {str(e)}")
    return {
        "cv": None,
        "status": {
            "code": 500,
            "message": str(e)
        }
    }

# @async_timed
def process_files(files, client, time_now):
    # Initialize BRILargeLanguageModel with API endpoint and key from .env

    
    # tasks = [parse_file(files[i], time_now) for i in range(len(files))]
    print("Making tasks")
    # responses = await asyncio.gather(*tasks, return_exceptions=True)
    responses = [parse_file(files[0], client, time_now)]
    return responses