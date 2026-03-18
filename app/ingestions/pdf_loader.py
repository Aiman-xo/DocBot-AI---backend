from pypdf import PdfReader

def extract_pdf_to_text(document):
    reader = PdfReader(document.file)

    text = ""

    for page in reader.pages:
        text+=page.extract_text()

    return text
