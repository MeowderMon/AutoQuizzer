import streamlit as st
import google.generativeai as genai
from file_parser import parse_file
from mcq_generator import generate_mcqs, generate_pdf
import re

# --- Gemini API Key Configuration ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- Page Setup ---
st.set_page_config(page_title="AutoQuizzer AI", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 AutoQuizzer AI</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Upload your study notes and generate MCQs using AI</h4>", unsafe_allow_html=True)
st.divider()

# --- State Initialization ---
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "mcqs_text" not in st.session_state:
    st.session_state.mcqs_text = ""
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# --- File Upload ---
uploaded_file = st.file_uploader("Upload a file (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
file_contents = ""

if uploaded_file:
    file_contents = parse_file(uploaded_file)
    st.markdown("#### 📘 Extracted Content")
    st.text_area("", file_contents, height=250)

    st.markdown("#### 🎯 Quiz Settings")
    col1, col2 = st.columns([1, 1])
    difficulty = col1.selectbox("Select Difficulty", ["Easy", "Medium", "Hard"])
    num_mcqs = col2.slider("Number of MCQs", min_value=5, max_value=20, value=10)

    st.divider()
    col3, col4 = st.columns([1, 1])
    generate_clicked = col3.button("⚡ Generate MCQs")
    regen_clicked = col4.button("🔁 Regenerate")

    def extract_mcq_blocks(text):
        # Regex to extract question, options, correct answer, and explanations per option
        pattern = (
            r"\*\*(\d+\..*?)\*\*\s*"                              # Question
            r"(.*?)(?=✅\s*Correct Answer:)"                      # Options block
            r"✅\s*Correct Answer:\s*([A-D])"                     # Correct answer
            r"(?:\s*📝\s*Explanation A:\s*(.*?))?"                # Explanation A
            r"(?:\s*📝\s*Explanation B:\s*(.*?))?"                # Explanation B
            r"(?:\s*📝\s*Explanation C:\s*(.*?))?"                # Explanation C
            r"(?:\s*📝\s*Explanation D:\s*(.*?))?"                # Explanation D
        )
        matches = re.findall(pattern, text, re.DOTALL)
        mcq_data = []
        for match in matches:
            question, options_block, answer, exp_a, exp_b, exp_c, exp_d = match
            options = re.findall(r"[A-D]\)?\.?\s*(.+)", options_block.strip())
            explanations = {
                "A": exp_a.strip() if exp_a else "",
                "B": exp_b.strip() if exp_b else "",
                "C": exp_c.strip() if exp_c else "",
                "D": exp_d.strip() if exp_d else "",
            }
            mcq_data.append({
                "question": question.strip(),
                "options": options,
                "answer": answer.strip(),
                "explanations": explanations
            })
        return mcq_data

    if generate_clicked or regen_clicked:
        with st.spinner("Generating questions using AI..."):
            try:
                mcqs = generate_mcqs(file_contents, num_questions=num_mcqs, difficulty=difficulty)
                quiz_data = extract_mcq_blocks(mcqs)
                if not quiz_data:
                    st.error("❌ MCQ format could not be parsed. Please try regenerating.")
                    st.session_state.quiz = None
                    st.session_state.mcqs_text = ""
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                else:
                    st.session_state.quiz = quiz_data
                    st.session_state.mcqs_text = mcqs
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
            except Exception as e:
                st.error(f"❌ Something went wrong:\n{e}")
                st.session_state.quiz = None
                st.session_state.mcqs_text = ""
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False

# --- Quiz UI ---
if st.session_state.quiz:
    st.markdown("### 🧪 Attempt the Quiz")
    all_answered = True
    for i, q in enumerate(st.session_state.quiz):
        st.markdown(f"**Q{i+1}. {q['question']}**")
        options = [
            "-- Select an answer --",
            f"A. {q['options'][0]}",
            f"B. {q['options'][1]}",
            f"C. {q['options'][2]}",
            f"D. {q['options'][3]}"
        ]

        prev_answer = st.session_state.user_answers.get(f"q{i}", options[0])
        index = options.index(prev_answer) if prev_answer in options else 0

        selected = st.radio(
            label="Your Answer:",
            options=options,
            key=f"q{i}",
            index=index,
            horizontal=False
        )
        st.session_state.user_answers[f"q{i}"] = selected
        st.markdown("---")

        if selected == options[0]:
            all_answered = False

    submit_disabled = not all_answered
    if submit_disabled:
        st.warning("Please answer all questions before submitting.")

    if st.button("✅ Submit Quiz", disabled=submit_disabled):
        st.session_state.quiz_submitted = True

    # --- Results Display ---
    if st.session_state.quiz_submitted:
        score = 0
        st.markdown("### 📊 Results")
        for i, q in enumerate(st.session_state.quiz):
            selected = st.session_state.user_answers[f"q{i}"]
            selected_letter = selected[0] if selected != "-- Select an answer --" else "?"
            correct = q["answer"]
            is_correct = selected_letter == correct
            result = "✅ Correct" if is_correct else f"❌ Wrong (Correct: {correct})"
            color = "green" if is_correct else "red"
            st.markdown(f"**Q{i+1}:** <span style='color:{color}'>{result}</span>", unsafe_allow_html=True)

            # Show explanation for the selected option if incorrect
            if not is_correct and q["explanations"].get(selected_letter):
                st.info(f"**Explanation for your answer ({selected_letter}):** {q['explanations'][selected_letter]}")

            # Always show explanation for the correct answer
            if q["explanations"].get(correct):
                st.success(f"**Explanation for the correct answer ({correct}):** {q['explanations'][correct]}")

            if is_correct:
                score += 1
        st.success(f"🎯 Score: {score} / {len(st.session_state.quiz)}")

        # PDF Download
        generate_pdf(st.session_state.mcqs_text)
        with open("mcqs_output.pdf", "rb") as f:
            st.download_button("📥 Download as PDF", f, file_name="AutoQuizzer_MCQs.pdf")

elif uploaded_file:
    st.info("Click 'Generate MCQs' to create your quiz.")

else:
    st.info("Upload a file above to get started.")
