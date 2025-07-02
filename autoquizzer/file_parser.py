import os
from pdfminer.high_level import extract_text
from docx import Document
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import tempfile

# Point to Tesseract executable (optional now, since you added it to PATH)
# pytesseract.pytesseract.tesseract_cmd = r'D:\ocr\tesseract.exe'

def parse_file(uploaded_file):
    file_type = uploaded_file.type
    text = ""

    if file_type == "text/plain":
        text = uploaded_file.read().decode("utf-8")

    elif file_type == "application/pdf":
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        text = extract_text("temp.pdf")

        # 🔁 If no extractable text found, use OCR
        if not text.strip():
            text = extract_text_from_scanned_pdf("temp.pdf")

        os.remove("temp.pdf")

    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with open("temp.docx", "wb") as f:
            f.write(uploaded_file.read())
        doc = Document("temp.docx")
        text = "\n".join([para.text for para in doc.paragraphs])
        os.remove("temp.docx")

    return text

def extract_text_from_scanned_pdf(pdf_path):
    extracted = ""
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(pdf_path, output_folder=temp_dir)
        for image in images:
            extracted += pytesseract.image_to_string(image)
    return extracted
