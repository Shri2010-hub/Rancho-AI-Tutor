import json
import os
import random
import datetime
from pathlib import Path

import streamlit as st

# ---------------------- Paths & Constants ----------------------
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path(".")
QUESTIONS_DIR = BASE_DIR / "questions"
SUBMISSIONS_DIR = BASE_DIR / "submissions"
SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_FILE = BASE_DIR / "progress.json"
CREATIVE_FILE = SUBMISSIONS_DIR / "creative_submissions.json"
PROJECT_FILE = SUBMISSIONS_DIR / "project_progress.json"

SUBJECTS = ["Maths", "Physics", "Chemistry", "Biology"]
EXAMS = ["JEE", "NEET"]

# ---------------------- Utilities (IO) ----------------------
def read_json(path, default):
    p = Path(path)
    if p.exists() and p.stat().st_size > 0:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def write_json(path, data):
    p = Path(path)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------------- Streamlit compatibility helpers ----------------------
def safe_rerun():
    """
    Use st.rerun() on modern Streamlit; fall back to experimental_rerun() if present.
    """
    try:
        st.rerun()
    except Exception:
        # older versions
        try:
            st.experimental_rerun()
        except Exception:
            # If neither exists, force a page reload by writing a tiny message (best-effort)
            st.experimental_set_query_params(reload=str(random.random()))

# ---------------------- Progress ----------------------
def load_progress():
    return read_json(PROGRESS_FILE, {"total_score": 0, "progress": {sub: 0 for sub in SUBJECTS}})

def save_progress(progress):
    write_json(PROGRESS_FILE, progress)

# ---------------------- Questions ----------------------
def load_questions(subject, exam):
    """
    Loads questions from questions/<subject_lower>.json and filters by exam.
    Supports two formats:
        A) options is a dict like {"A": "...", "B": "..."}
        B) options is a list like ["...","...","...","..."]
    """
    file_map = {
        "Maths": "maths",
        "Physics": "physics",
        "Chemistry": "chemistry",
        "Biology": "biology",
    }
    filename = file_map.get(subject, subject.lower()) + ".json"
    filepath = QUESTIONS_DIR / filename

    if not filepath.exists():
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter by exam type; be tolerant of case
    filtered = [q for q in data if str(q.get("exam", "")).upper() == exam.upper()]

    # Normalize options to dict with A/B/C/D keys internally for UI
    normalized = []
    for q in filtered:
        opt = q.get("options", {})
        if isinstance(opt, list):
            # convert list -> dict
            letters = ["A", "B", "C", "D"][: len(opt)]
            opt = {letters[i]: opt[i] for i in range(len(opt))}
        normalized.append({
            "id": q.get("id"),
            "subject": q.get("subject", subject),
            "exam": q.get("exam", exam),
            "question": q.get("question", ""),
            "options": opt,
            "answer": q.get("answer")  # letter like "A"
        })
    return normalized

# ---------------------- Creative Mode (Prompts & Feedback) ----------------------
CREATIVE_PROMPTS = {
    "Maths": [
        "Invent a real-life situation where quadratic equations naturally arise. Explain how you’d model it.",
        "Design a puzzle using arithmetic progressions that has a surprising twist.",
        "Explain derivatives to a 10-year-old using a story or analogy."
    ],
    "Physics": [
        "Design a home experiment to show Newton’s Third Law using kitchen items. Outline steps and observations.",
        "What if gravity were 20% stronger? Predict 3 changes in sports or architecture.",
        "Explain wave–particle duality using a simple metaphor and a drawing plan."
    ],
    "Chemistry": [
        "Create a kitchen-safe experiment to demonstrate an acid-base reaction. Include safety notes.",
        "Imagine a world where hydrogen bonds didn’t exist. How would life change?",
        "Explain Le Chatelier’s principle with a story about balance and choices."
    ],
    "Biology": [
        "If humans could photosynthesize, how would city life and school schedules change?",
        "Design a simple at-home model to explain DNA replication.",
        "Propose a school garden plan that boosts biodiversity and learning."
    ],
}

def simple_creative_feedback(text):
    """
    Lightweight rubric-based feedback (no external APIs).
    Awards badges and gives formative comments.
    """
    length = len(text.strip())
    badges = []

    # Heuristics for feedback
    if length > 600:
        badges.append("Depth 💡")
    if any(k in text.lower() for k in ["because", "therefore", "hence", "so that"]):
        badges.append("Reasoning 🧠")
    if any(k in text.lower() for k in ["imagine", "what if", "suppose", "let's assume"]):
        badges.append("Imagination 🎨")
    if any(k in text.lower() for k in ["experiment", "steps", "hypothesis", "observe", "materials"]):
        badges.append("Scientific Method 🔬")
    if any(k in text.lower() for k in ["design", "prototype", "sketch", "diagram", "model"]):
        badges.append("Design Thinking 🛠️")

    comments = []
    if length < 120:
        comments.append("Try expanding with examples or a short scenario.")
    else:
        comments.append("Good depth—consider adding a quick summary at the end.")

    if "experiment" in text.lower() and "safety" not in text.lower():
        comments.append("Add a brief safety note if an experiment is involved.")

    if not badges:
        comments.append("Nice start—push for more details, ‘what if’ scenarios, or a small diagram plan.")

    return badges, comments

def load_creative_submissions():
    return read_json(CREATIVE_FILE, [])

def save_creative_submission(entry):
    data = load_creative_submissions()
    data.append(entry)
    write_json(CREATIVE_FILE, data)

# ---------------------- Projects ----------------------
PROJECT_TEMPLATES = [
    {
        "id": "proj_solar_cooker",
        "title": "Build a Simple Solar Cooker (Physics + Design)",
        "subject": "Physics",
        "steps": [
            "Research how solar cookers concentrate sunlight.",
            "Sketch your design (box, foil, plastic wrap).",
            "List materials and cost.",
            "Build a prototype and record temperature over 20 minutes.",
            "Reflect: how would you improve it?"
        ]
    },
    {
        "id": "proj_ecosystem_terrarium",
        "title": "Create a Closed Terrarium Ecosystem (Biology + Ecology)",
        "subject": "Biology",
        "steps": [
            "Plan components: soil, small plants/moss, stones, water.",
            "Explain energy flow and cycles (water, nutrients) inside.",
            "Build the terrarium; add observations for 2 weeks.",
            "Identify any imbalance and propose fixes.",
            "Share photos and a 5-sentence reflection."
        ]
    },
    {
        "id": "proj_titration_at_home",
        "title": "Kitchen Acid–Base ‘Titration’ (Chemistry + Inquiry)",
        "subject": "Chemistry",
        "steps": [
            "Create a red-cabbage indicator (or use litmus strips).",
            "Pick two household solutions to compare (vinegar, baking soda solution).",
            "Design a step-by-step neutralization attempt.",
            "Record color changes and estimate relative acidity/basicity.",
            "Reflect on sources of error and how to improve accuracy."
        ]
    },
    {
        "id": "proj_real_life_quadratics",
        "title": "Quadratics in Real Life (Maths + Modeling)",
        "subject": "Maths",
        "steps": [
            "Find a real problem involving a parabolic path or area optimization.",
            "Model it as a quadratic function.",
            "Solve and interpret the roots/vertex in context.",
            "Validate with a quick simulation or estimates.",
            "Present your model and limitations."
        ]
    }
]

def load_project_progress():
    return read_json(PROJECT_FILE, {})

def save_project_progress(data):
    write_json(PROJECT_FILE, data)

# ---------------------- Exam Quiz (stateful) ----------------------
def init_quiz_state():
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "quiz_subject" not in st.session_state:
        st.session_state.quiz_subject = None
    if "quiz_exam" not in st.session_state:
        st.session_state.quiz_exam = None
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "current_q" not in st.session_state:
        st.session_state.current_q = 0
    if "score" not in st.session_state:
        st.session_state.score = 0

def reset_quiz():
    st.session_state.quiz_started = False
    st.session_state.quiz_subject = None
    st.session_state.quiz_exam = None
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.score = 0

# ---------------------- UI: Exam Practice ----------------------
def tab_exam():
    st.subheader("📝 Exam Practice (JEE/NEET)")
    progress = load_progress()

    # Sidebar mini dashboard
    with st.sidebar:
        st.markdown("### 📊 Your Progress")
        st.write(f"**Total Score:** {progress['total_score']}")
        st.write(progress["progress"])

    init_quiz_state()

    if not st.session_state.quiz_started:
        subject = st.selectbox("Choose Subject", SUBJECTS, key="sel_subject")
        exam = st.selectbox("Preparing for", EXAMS, key="sel_exam")
        num_questions = st.slider("How many questions?", 5, 20, 5, key="sel_count")

        if st.button("Start Quiz"):
            qs = load_questions(subject, exam)
            if not qs:
                st.error(f"No questions found for {subject} ({exam}). Put a JSON at questions/{subject.lower()}.json")
                return

            selected = random.sample(qs, min(num_questions, len(qs)))
            # shuffle options per question (keep answer mapping correct)
            for q in selected:
                # Convert to ordered list for consistent display mapping
                labels = list(q["options"].keys())
                values = list(q["options"].values())
                paired = list(zip(labels, values))
                random.shuffle(paired)
                # rebuild options & keep labels with their values (we'll check by label)
                new_labels = [p[0] for p in paired]
                new_values = [p[1] for p in paired]
                q["options"] = {new_labels[i]: new_values[i] for i in range(len(paired))}
                # answer remains the original label; it will still exist as a key in q["options"] after shuffle

            st.session_state.quiz_started = True
            st.session_state.quiz_subject = subject
            st.session_state.quiz_exam = exam
            st.session_state.questions = selected
            st.session_state.current_q = 0
            st.session_state.score = 0
    else:
        q_index = st.session_state.current_q
        questions = st.session_state.questions

        if q_index < len(questions):
            q = questions[q_index]
            st.markdown(f"**Q{q_index+1}: {q['question']}**")

            labels = list(q["options"].keys())
            values = list(q["options"].values())

            # radio returns an index; show values; store key name stable per question
            choice = st.radio(
                "Choose your answer:",
                options=list(range(1, len(values) + 1)),
                format_func=lambda x: values[x - 1],
                key=f"q_{q_index}"
            )

            if st.button("Submit Answer", key=f"submit_{q_index}"):
                chosen_label = labels[choice - 1]
                if chosen_label == q["answer"]:
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                else:
                    # show correct option value if available
                    correct_value = q["options"].get(q["answer"], "(answer label not found)")
                    st.error(f"❌ Wrong! Correct answer: {correct_value}")

                st.session_state.current_q += 1
                safe_rerun()

        else:
            st.success(f"🎯 Quiz Finished! Score: {st.session_state.score}/{len(questions)}")

            # Update persistent progress
            progress["total_score"] += st.session_state.score
            subj = st.session_state.quiz_subject or questions[0].get("subject", "Unknown")
            if subj not in progress["progress"]:
                progress["progress"][subj] = 0
            progress["progress"][subj] += st.session_state.score
            save_progress(progress)

            col1, col2 = st.columns(2)
            if col1.button("Take Another Quiz"):
                reset_quiz()
                safe_rerun()
            if col2.button("Back to Home"):
                reset_quiz()
                safe_rerun()

# ---------------------- UI: Creative Mode ----------------------
def tab_creative():
    st.subheader("🎨 Creative Mode (Ken Robinson–inspired)")

    st.markdown(
        "Balance exam practice with **divergent thinking**. "
        "Pick a subject, get a creative prompt, and write your idea. "
        "You’ll receive formative feedback and badges."
    )

    subject = st.selectbox("Subject for your creative prompt", SUBJECTS, key="creative_subject")
    prompt_pool = CREATIVE_PROMPTS.get(subject, [])
    if not prompt_pool:
        st.info("No prompts found. Using a general prompt.")
        prompt_pool = ["Describe something you’re curious about in this subject and propose a way to explore it."]

    if "current_prompt_idx" not in st.session_state:
        st.session_state.current_prompt_idx = 0

    cols = st.columns([1, 1, 2])
    if cols[0].button("🎲 New Prompt"):
        st.session_state.current_prompt_idx = random.randrange(len(prompt_pool))
    cols[1].button("Keep This Prompt")  # just for UX spacing :)

    prompt = prompt_pool[st.session_state.current_prompt_idx]
    st.markdown(f"**Prompt:** {prompt}")

    idea = st.text_area("Your response (you can paste a photo link/diagram plan too):", height=220, key="creative_text")

    if st.button("Get Feedback & Save"):
        if not idea.strip():
            st.warning("Write something before submitting.")
            return
        badges, comments = simple_creative_feedback(idea)
        if badges:
            st.success("🏅 Badges: " + " · ".join(badges))
        for c in comments:
            st.info("💬 " + c)

        # Save submission
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "subject": subject,
            "prompt": prompt,
            "text": idea
        }
        save_creative_submission(entry)
        st.success("Saved your creative submission!")

    # Show history
    st.markdown("---")
    st.markdown("### 🗂️ Your Creative Submissions (latest 5)")
    history = load_creative_submissions()
    if history:
        for item in list(reversed(history))[:5]:
            st.markdown(f"- **{item['subject']}** · *{item['timestamp']}*  \n  _{item['prompt']}_")
    else:
        st.write("No submissions yet—try one!")

# ---------------------- UI: Projects ----------------------
def tab_projects():
    st.subheader("🛠️ Project Hub (Learn by Doing)")
    st.write("Pick a project, follow steps, and upload evidence (images/notes).")

    project_ids = [p["id"] for p in PROJECT_TEMPLATES]
    titles = {p["id"]: p["title"] for p in PROJECT_TEMPLATES}
    by_id = {p["id"]: p for p in PROJECT_TEMPLATES}

    selected_title = st.selectbox("Choose a project", [titles[i] for i in project_ids])
    # find id
    selected_id = [pid for pid in project_ids if titles[pid] == selected_title][0]
    proj = by_id[selected_id]

    st.markdown(f"**Subject:** {proj['subject']}")
    st.markdown(f"**Project:** {proj['title']}")

    progress = load_project_progress()
    if selected_id not in progress:
        progress[selected_id] = {"completed": [False] * len(proj["steps"]), "notes": ""}

    # Steps checklist
    st.markdown("#### Steps")
    updated_completed = []
    for i, step in enumerate(proj["steps"]):
        checked = st.checkbox(step, value=progress[selected_id]["completed"][i], key=f"step_{selected_id}_{i}")
        updated_completed.append(checked)

    # Notes field
    notes = st.text_area("Notes / Observations / Reflections", value=progress[selected_id].get("notes", ""), height=180, key=f"notes_{selected_id}")

    # Upload evidence (optional)
    upload = st.file_uploader("Upload a photo or PDF (optional)", type=["png", "jpg", "jpeg", "pdf"], key=f"upload_{selected_id}")
    if upload is not None:
        save_path = SUBMISSIONS_DIR / f"{selected_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{upload.name}"
        with open(save_path, "wb") as f:
            f.write(upload.read())
        st.success(f"Uploaded: {save_path.name}")

    # Save progress
    if st.button("Save Project Progress"):
        progress[selected_id]["completed"] = updated_completed
        progress[selected_id]["notes"] = notes
        save_project_progress(progress)
        st.success("Project progress saved!")

    # Completion meter
    done = sum(updated_completed)
    total = len(updated_completed)
    st.progress(int(100 * done / max(1, total)))
    st.write(f"Completion: **{done}/{total}** steps")

# ---------------------- App ----------------------
def main():
    st.set_page_config(page_title="AI Personal Tutor — Creativity + Exam", page_icon="🎓", layout="wide")

    st.title("🎓 AI Personal Tutor")
    st.caption("Prep for **JEE/NEET** and grow your **creativity** — inspired by Sir Ken Robinson.")

    # Daily creative prompt card
    st.markdown("---")
    colA, colB = st.columns([3, 2])
    with colA:
        st.markdown("#### 🌟 Daily Creative Prompt")
        subj = random.choice(SUBJECTS)
        prompt = random.choice(CREATIVE_PROMPTS[subj])
        st.write(f"**{subj}:** {prompt}")
    with colB:
        prog = load_progress()
        exam_total = prog["total_score"]
        creative_count = len(load_creative_submissions())
        st.markdown("#### 📈 Dual Progress")
        st.write(f"**Exam Readiness (Total Score):** {exam_total}")
        st.progress(min(1.0, exam_total / 100))  # arbitrary cap
        st.write(f"**Creative Growth (Submissions):** {creative_count}")
        st.progress(min(1.0, creative_count / 20))  # arbitrary cap

    st.markdown("---")
    tabs = st.tabs(["📝 Exam Practice", "🎨 Creative Mode", "🛠️ Projects"])

    with tabs[0]:
        tab_exam()
    with tabs[1]:
        tab_creative()
    with tabs[2]:
        tab_projects()

if __name__ == "__main__":
    main()
