from pypdf import PdfReader

def extract_pdf_to_text(document_or_path):
    # Check if a string file path was passed instead of an UploadFile object
    if isinstance(document_or_path, str):
        reader = PdfReader(document_or_path)
    else:
        reader = PdfReader(document_or_path.file)

    text = ""

    for page in reader.pages:
        text+=page.extract_text()

    return text
