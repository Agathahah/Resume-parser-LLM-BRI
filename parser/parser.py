"""Turn an uploaded CV into structured JSON with an LLM."""

import json
import logging
import os
import re
from pathlib import Path
from time import time

from dotenv import load_dotenv

from parser.document import read_docx, read_pdf

load_dotenv()
log = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompt.txt"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


def read_file_content(file):
    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        return read_pdf(file)
    if extension in ("doc", "docx"):
        return read_docx(file)
    raise ValueError(f"Extension .{extension} not allowed; use {sorted(ALLOWED_EXTENSIONS)}")


def read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def extract_json(answer: str):
    """Parse the model reply. Accepts a bare object, a one-element list, or either inside ``` fences."""
    text = answer.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    data = json.loads(text)
    if isinstance(data, list):
        if len(data) != 1 or not isinstance(data[0], dict):
            raise ValueError("Expected one JSON object for one CV")
        data = data[0]
    if not isinstance(data, dict):
        raise ValueError("Model reply is not a JSON object")
    return data


def build_messages(cv_text: str):
    return [
        {"role": "system", "content": "You are CV Parsing master"},
        {"role": "user", "content": read_prompt()},
        {"role": "user", "content": f"CV\n{cv_text}\n\n"},
    ]


def parse_file(file, client, time_now):
    """Parse one file. Never logs CV text: it is personal data."""
    try:
        cv_text = read_file_content(file)
        sampling_params = {
            "temperature": 0.0,
            "top_p": 0.95,
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
        }
        response = client.create_response(messages=build_messages(cv_text), sampling_params=sampling_params)
        if response.get("function_call"):
            cv = response["function_call"][0]
        else:
            cv = extract_json(response["llm_answer"])
        log.info("parsed %s in %.2fs", file.filename, time() - time_now)
        return {"cv": cv, "status": {"code": 200, "message": "CV parsed successfully."}}
    except Exception as exc:  # report per-file failure instead of failing the whole request
        log.warning("failed to parse %s: %s", getattr(file, "filename", "?"), type(exc).__name__)
        return {"cv": None, "status": {"code": 500, "message": str(exc)}}


def process_files(files, client, time_now):
    return [parse_file(f, client, time_now) for f in files]
