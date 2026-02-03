import os
import PyPDF2
import docx
import io

def extract_text_from_file(file_stream, filename):
    """
    Extracts text from various file formats (.pdf, .docx, .doc, .txt).
    """
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.pdf':
            reader = PyPDF2.PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
            
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(file_stream)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text.strip()
            
        elif ext == '.txt':
            # Ensure the stream is at the beginning
            file_stream.seek(0)
            return file_stream.read().decode('utf-8', errors='ignore').strip()
            
        else:
            return ""
            
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        return ""
