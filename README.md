# Resume Parser with an LLM (BRI internship prototype)

A Flask app that turns uploaded CVs (PDF or Word) into structured JSON by prompting a large language model. First built during my AI Research internship at Bank Rakyat Indonesia (Aug 2024 – Jan 2025); this public version runs against any OpenAI-compatible endpoint, or fully offline with a fake model.

## How it works

```
upload (PDF / DOCX) ──► text extraction (pypdf / docx2txt)
                    ──► prompt.txt (JSON schema: name, contact, experience, education, skills …)
                    ──► LLM chat completion (temperature 0)
                    ──► JSON extracted from the reply ──► returned per file with a status code
```

| File | Role |
|---|---|
| `parser/llm_clients.py` | `OpenAICompatibleLLM` (OpenAI, Groq, Ollama, vLLM …), `FakeLLM` (offline), and `build_client_from_env()` |
| `parser/bri_llm.py` | Client for the internal BRI LLM service as used during the internship. Its request/response format is **not** OpenAI's (`messages` + `sampling_params` in, `data.llm_answer` out). It only works inside the BRI network and is kept for reference. |
| `parser/parser.py` | File reading, prompt assembly, JSON extraction (`extract_json` accepts bare JSON, a one-item list, or a fenced block), per-file error reporting |
| `app.py` | Flask route: `GET /` upload page, `POST /` with form field `resumes` |
| `templates/result.html` | Static preview of the output format, filled with **fictional** data |

## Design decision: prompting instead of a trained NER model

The first plan was a custom named-entity-recognition model. CV layouts vary too much (tables, columns, mixed Indonesian/English) for the amount of labelled data available, so the project moved to schema-guided prompting with temperature 0 for repeatable output. Trade-offs: no training data needed and new fields are added by editing the schema, but each CV costs an LLM call, the output must be validated, and quality depends on the model behind the endpoint.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # LLM_PROVIDER=fake works with no key
python -m pytest -q             # 11 passed
flask --app app run             # open http://127.0.0.1:5000
```

To use a real model, set in `.env`:

```bash
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1      # or http://localhost:11434/v1 for Ollama
LLM_API_KEY=...
LLM_MODEL=<a model id your endpoint serves>
```

## Status and limitations

- Prototype. Field-level accuracy has not been measured; the next step is precision/recall per field on 50–100 hand-labelled CVs (fictional or consented).
- No JSON-schema validation of the model output and no retry on malformed JSON (a malformed reply returns `cv: null` with status 500 for that file).
- Flask development server; no authentication or rate limiting. Upload size is capped at 10 MB.

## Privacy

CV text is never logged. Real CVs, `.pdf`/`.docx` files and logs are git-ignored. Test and demo data are fictional.
