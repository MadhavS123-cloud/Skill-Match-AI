import os
import PyPDF2
import docx

def extract_text_from_file(file_stream, filename):
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == '.pdf':
            reader = PyPDF2.PdfReader(file_stream)
            return "".join(page.extract_text() + "\n" for page in reader.pages).strip()
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(file_stream)
            return "\n".join(para.text for para in doc.paragraphs).strip()
        elif ext == '.txt':
            file_stream.seek(0)
            return file_stream.read().decode('utf-8', errors='ignore').strip()
    except Exception:
        pass
    return ""
