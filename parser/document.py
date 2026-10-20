import docx2txt
from pypdf import PdfReader


def read_pdf(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    return "".join(page.extract_text() or "" for page in reader.pages)


def read_docx(docx_file) -> str:
    return docx2txt.process(docx_file)
