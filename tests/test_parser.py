import io
import json

import pytest

from parser import parser as P
from parser.llm_clients import FAKE_CV, FakeLLM, OpenAICompatibleLLM, build_client_from_env


class Upload(io.BytesIO):
    def __init__(self, name, data=b"x"):
        super().__init__(data)
        self.filename = name


@pytest.mark.parametrize("reply", [
    json.dumps(FAKE_CV),
    "[" + json.dumps(FAKE_CV) + "]",
    "```json\n[" + json.dumps(FAKE_CV) + "]\n```",
    "Here you go:\n```\n" + json.dumps(FAKE_CV) + "\n```",
])
def test_extract_json_accepts_common_reply_shapes(reply):
    assert P.extract_json(reply)["email"] == FAKE_CV["email"]


def test_extract_json_rejects_two_cvs():
    with pytest.raises(ValueError):
        P.extract_json(json.dumps([FAKE_CV, FAKE_CV]))


def test_parse_file_success_and_prompt_contains_cv_text(monkeypatch):
    monkeypatch.setattr(P, "read_file_content", lambda f: "Nama: Budi\nPython, SQL")
    llm = FakeLLM()
    out = P.parse_file(Upload("cv.pdf"), llm, 0.0)
    assert out["status"]["code"] == 200 and out["cv"]["name"] == FAKE_CV["name"]
    assert "Python, SQL" in llm.calls[0][-1]["content"]


def test_parse_file_reports_bad_json_without_crashing(monkeypatch):
    monkeypatch.setattr(P, "read_file_content", lambda f: "text")
    out = P.parse_file(Upload("cv.pdf"), FakeLLM(answer="not json"), 0.0)
    assert out["cv"] is None and out["status"]["code"] == 500


def test_unsupported_extension_is_rejected():
    out = P.parse_file(Upload("cv.exe"), FakeLLM(), 0.0)
    assert out["cv"] is None and "not allowed" in out["status"]["message"]


def test_openai_client_sends_bearer_and_maps_reply(monkeypatch):
    seen = {}

    class R:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": "{\"name\": \"A\"}"}}]}

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, body=json, headers=headers)
        return R()

    monkeypatch.setattr("parser.llm_clients.requests.post", fake_post)
    c = OpenAICompatibleLLM("http://localhost:11434/v1/", "k", "m")
    out = c.create_response([{"role": "user", "content": "hi"}], sampling_params={"temperature": 0, "foo": 1})
    assert seen["url"] == "http://localhost:11434/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer k"
    assert seen["body"] == {"model": "m", "messages": [{"role": "user", "content": "hi"}], "temperature": 0}
    assert out == {"function_call": None, "llm_answer": "{\"name\": \"A\"}"}


def test_factory_requires_model_for_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(ValueError):
        build_client_from_env()


def test_flask_endpoint_with_fake_provider(monkeypatch):
    import app as A

    monkeypatch.setattr(P, "read_file_content", lambda f: "text")
    res = A.app.test_client().post(
        "/", data={"resumes": (io.BytesIO(b"%PDF"), "cv.pdf")}, content_type="multipart/form-data"
    )
    assert res.status_code == 200
    assert res.get_json()["data"][0]["cv"]["email"] == "kandidat@example.com"
    assert A.app.test_client().post("/", data={}).status_code == 400
