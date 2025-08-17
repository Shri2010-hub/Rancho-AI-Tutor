
import streamlit as st
import json, os, random
from engine import load_questions, get_subjects, AdaptiveSelector, evaluate_answer, record_event, compute_report

st.set_page_config(page_title="AI Personal Tutor", page_icon="🎓", layout="centered")

st.title("🎓 AI Personal Tutor")
user = st.text_input("Your name", value="Student").strip() or "Student"

tab1, tab2 = st.tabs(["Practice Quiz", "Progress Dashboard"])

with tab1:
    questions = load_questions()
    subjects = get_subjects(questions)
    subject = st.selectbox("Choose subject", subjects, index=0)
    n = st.number_input("Number of questions", min_value=3, max_value=20, value=7, step=1)

    if "selector" not in st.session_state:
        st.session_state.selector = AdaptiveSelector(start_difficulty=2)
        st.session_state.q_count = 0
        st.session_state.score = 0
        st.session_state.current_q = None
        st.session_state.logs = []

    def new_question():
        st.session_state.current_q = st.session_state.selector.pick(questions, subject)

    if st.button("Start / Next Question"):
        new_question()

    q = st.session_state.current_q
    if q:
        st.markdown(f"**Q{st.session_state.q_count+1}** — *{q['subject']} · {q['topic']} · ★{q.get('difficulty',1)}*")
        st.write(q["question"])
        user_input = None
        if q["type"] == "mcq":
            opts = q.get("options", [])
            user_input = st.radio("Choose one", opts, index=None)
        elif q["type"] == "numeric":
            user_input = st.text_input("Your answer (number allowed, e.g., 0.5 or 1/2)")
        else:
            user_input = st.text_input("Your answer (text)")

        if st.button("Submit"):
            if user_input is None or str(user_input).strip() == "":
                st.warning("Please provide an answer.")
            else:
                ok, corr = evaluate_answer(q, str(user_input))
                st.session_state.selector.update(ok)
                record_event(user, subject, q, ok)
                st.session_state.q_count += 1
                if ok:
                    st.session_state.score += 1
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong. Correct: {corr}")
                    st.info(q.get("explanation","Review this concept."))
                if st.session_state.q_count >= n:
                    st.balloons()
                    st.write(f"**Session Done! Score: {st.session_state.score}/{n}**")
                    st.session_state.q_count = 0
                    st.session_state.score = 0

with tab2:
    if st.button("Refresh Report"):
        pass
    rep = compute_report(user)
    st.subheader(f"Overall Accuracy: {rep['accuracy']}% (over {rep['total']} attempts)")
    if rep["topic_stats"]:
        st.write("**By Topic**")
        st.table(rep["topic_stats"])
    if rep["recommendations"]:
        st.write("**Recommendations**")
        for r in rep["recommendations"]:
            st.write("• " + r)
    st.caption("Progress is stored in `data/progress.json`.")
