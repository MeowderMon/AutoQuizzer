import google.generativeai as genai
from fpdf import FPDF
import re

def remove_emojis(text):
    # Remove emojis like ✅, ❌ etc.
    return re.sub(r'[^\x00-\x7F]+', '', text)

# Load model
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

def generate_mcqs(content, num_questions=10, difficulty="Medium"):
    prompt = f"""
You're an AI MCQ generator trained to work with handwritten-style, messy, student notes.

From the notes below, generate **{num_questions}** **{difficulty}** level MCQs.

🧠 Format:
- Question with 4 options (A, B, C, D)
- Show answer like: ✅ Correct Answer: B
- After each question, provide a short explanation for **each option**, like:
  📝 Explanation A: [explanation for option A]
  📝 Explanation B: [explanation for option B]
  📝 Explanation C: [explanation for option C]
  📝 Explanation D: [explanation for option D]

📄 Notes:
---------
{content}
"""
    response = model.generate_content(prompt)
    return response.text

def generate_pdf(mcq_text):
    cleaned_text = remove_emojis(mcq_text)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in cleaned_text.split('\n'):
        pdf.multi_cell(0, 10, line)

    pdf.output("mcqs_output.pdf")
