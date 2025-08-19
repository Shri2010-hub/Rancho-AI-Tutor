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
        A) options is a dict like {"A": "...", "B": "...}
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
        "Explain derivatives to a 10-year-old using a story or analogy.",
        "Imagine you’re an architect—how would you use geometry to design a futuristic building?",
        "Create a riddle where the answer requires solving a system of equations.",
        "Design a math game where winning depends on probability tricks."
    ],
    "Physics": [
        "Design a home experiment to show Newton’s Third Law using kitchen items. Outline steps and observations.",
        "What if gravity were 20% stronger? Predict 3 changes in sports or architecture.",
        "Explain wave–particle duality using a simple metaphor and a drawing plan.",
        "Imagine if light traveled 10 times slower—how would daily life and technology change?",
        "Propose a design for a vehicle that works without friction. What would be its strengths and weaknesses?",
        "Write a short sci-fi story where time dilation affects a student’s exam preparation."
    ],
    "Chemistry": [
        "Create a kitchen-safe experiment to demonstrate an acid-base reaction. Include safety notes.",
        "Imagine a world where hydrogen bonds didn’t exist. How would life change?",
        "Explain Le Chatelier’s principle with a story about balance and choices.",
        "Design a fictional element—describe its properties, uses, and dangers.",
        "Propose a green chemistry solution to reduce plastic waste in daily life.",
        "What if humans had built-in pH meters? How would medicine and food culture change?"
    ],
    "Biology": [
        "If humans could photosynthesize, how would city life and school schedules change?",
        "Design a simple at-home model to explain DNA replication.",
        "Propose a school garden plan that boosts biodiversity and learning.",
        "Imagine humans had night vision like owls—how would education and work schedules shift?",
        "Write a story from the point of view of a cell during cell division.",
        "Create a survival guide for humans living underwater permanently."
    ],
    "English": [
        "Write a diary entry from the perspective of your future self 20 years from now.",
        "Invent a new word and explain how people would start using it in daily life.",
        "Rewrite a famous fairy tale as a science-fiction story.",
        "Describe a classroom where students learn only through storytelling.",
        "If emojis were a full language, how would Shakespeare write Romeo and Juliet?",
        "Write a debate speech arguing whether AI should be allowed to write novels."
    ]
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
    # ---------------- Physics ----------------
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
        "id": "proj_water_rocket",
        "title": "Make a Water Rocket (Physics + Engineering)",
        "subject": "Physics",
        "steps": [
            "Research Newton’s Third Law in rocket propulsion.",
            "Design a water rocket using a plastic bottle.",
            "Add fins and a nose cone for stability.",
            "Launch safely outdoors and record flight height.",
            "Reflect: how nozzle size and water volume affected performance."
        ]
    },
    {
        "id": "proj_pendulum_timer",
        "title": "Pendulum as a Timer",
        "subject": "Physics",
        "steps": [
            "Set up a pendulum using a string and weight.",
            "Measure time period with different lengths.",
            "Compare with theoretical formula T = 2π√(L/g).",
            "Test if pendulum can keep steady time for 1 minute.",
            "Reflect on why pendulums are used in clocks."
        ]
    },
    {
        "id": "proj_diy_electric_motor",
        "title": "Build a Simple Electric Motor",
        "subject": "Physics",
        "steps": [
            "Research how electromagnetism works.",
            "Gather coil, magnet, battery, and safety pins.",
            "Wind the coil and mount it between supports.",
            "Connect battery and observe rotation.",
            "Reflect on how efficiency could be improved."
        ]
    },
    {
        "id": "proj_periscope",
        "title": "Make a Periscope (Optics)",
        "subject": "Physics",
        "steps": [
            "Research how mirrors reflect light.",
            "Design a periscope with two mirrors at 45°.",
            "Assemble using cardboard and mirrors.",
            "Test to look over obstacles.",
            "Reflect on its use in submarines."
        ]
    },
    {
        "id": "proj_diy_electromagnet",
        "title": "Create an Electromagnet",
        "subject": "Physics",
        "steps": [
            "Wrap insulated wire around an iron nail.",
            "Connect ends to a battery.",
            "Test how many paperclips it can lift.",
            "Experiment with coil turns and voltage.",
            "Reflect on electromagnets in daily life."
        ]
    },
    {
        "id": "proj_sound_resonance",
        "title": "Resonance in Sound",
        "subject": "Physics",
        "steps": [
            "Fill glass bottles with varying water levels.",
            "Blow across tops to produce sound.",
            "Measure pitch and compare with water level.",
            "Plot frequency vs. air column length.",
            "Reflect on resonance in music instruments."
        ]
    },
    {
        "id": "proj_parachute",
        "title": "Parachute Experiment (Air Resistance)",
        "subject": "Physics",
        "steps": [
            "Design a parachute using cloth/plastic and strings.",
            "Drop it with a small weight.",
            "Measure fall time vs. parachute size.",
            "Test stability by changing shapes.",
            "Reflect on drag forces and real parachutes."
        ]
    },
    {
        "id": "proj_diy_barometer",
        "title": "Make a Barometer",
        "subject": "Physics",
        "steps": [
            "Stretch balloon over jar opening.",
            "Fix straw pointer on top.",
            "Place against a scale on wall.",
            "Observe pointer movement with weather changes.",
            "Reflect on atmospheric pressure role in storms."
        ]
    },
    {
        "id": "proj_catapult",
        "title": "Build a Catapult (Projectile Motion)",
        "subject": "Physics",
        "steps": [
            "Design a catapult using sticks and rubber bands.",
            "Launch small objects safely.",
            "Measure range at different launch angles.",
            "Compare with theoretical parabolic motion.",
            "Reflect on angle for maximum distance."
        ]
    },

    # ---------------- Chemistry ----------------
    {
        "id": "proj_titration_at_home",
        "title": "Kitchen Acid–Base ‘Titration’",
        "subject": "Chemistry",
        "steps": [
            "Create a red-cabbage indicator (or use litmus strips).",
            "Pick two household solutions to compare (vinegar, baking soda solution).",
            "Design a step-by-step neutralization attempt.",
            "Record color changes and estimate acidity/basicity.",
            "Reflect on sources of error."
        ]
    },
    {
        "id": "proj_crystal_growing",
        "title": "Grow Salt Crystals",
        "subject": "Chemistry",
        "steps": [
            "Dissolve salt in hot water until saturated.",
            "Suspend a thread inside the solution.",
            "Leave undisturbed for days.",
            "Observe crystal growth.",
            "Reflect on crystallization process."
        ]
    },
    {
        "id": "proj_rust_prevention",
        "title": "Investigate Rust Prevention",
        "subject": "Chemistry",
        "steps": [
            "Take iron nails and expose them in salt water, oil, paint.",
            "Observe rusting speed.",
            "Compare results across conditions.",
            "Explain role of oxygen, water, salt.",
            "Reflect on corrosion protection."
        ]
    },
    {
        "id": "proj_homemade_plastic",
        "title": "Make Bioplastic from Milk",
        "subject": "Chemistry",
        "steps": [
            "Heat milk and add vinegar to curdle.",
            "Strain to get casein lumps.",
            "Mold into shape and dry.",
            "Test hardness after a few days.",
            "Reflect on bioplastics in sustainability."
        ]
    },
    {
        "id": "proj_candle_experiment",
        "title": "Candle and Oxygen Experiment",
        "subject": "Chemistry",
        "steps": [
            "Light a candle and cover with glass jar.",
            "Measure time until it extinguishes.",
            "Repeat with different jar sizes.",
            "Relate to oxygen consumption.",
            "Reflect on combustion chemistry."
        ]
    },
    {
        "id": "proj_homemade_pH_paper",
        "title": "Make Homemade pH Paper",
        "subject": "Chemistry",
        "steps": [
            "Soak paper strips in red cabbage extract.",
            "Dry and test on vinegar, soap, juice.",
            "Compare color changes.",
            "Create a pH color scale.",
            "Reflect on acid-base indicators."
        ]
    },
    {
        "id": "proj_diy_fire_extinguisher",
        "title": "DIY Fire Extinguisher",
        "subject": "Chemistry",
        "steps": [
            "Mix baking soda and vinegar in a bottle.",
            "Channel CO₂ gas to extinguish small candle flame.",
            "Test effectiveness.",
            "Relate to CO₂ fire extinguishers.",
            "Reflect on chemical safety."
        ]
    },
    {
        "id": "proj_metal_reactivity",
        "title": "Reactivity Series of Metals",
        "subject": "Chemistry",
        "steps": [
            "Take pieces of zinc, copper, iron.",
            "Dip in salt solution and record reaction.",
            "Compare displacement reactions.",
            "Rank metals by reactivity.",
            "Reflect on real-world applications."
        ]
    },
    {
        "id": "proj_solubility_test",
        "title": "Test Solubility of Substances",
        "subject": "Chemistry",
        "steps": [
            "Choose sugar, salt, sand, chalk.",
            "Mix with hot and cold water.",
            "Observe solubility differences.",
            "Record time to dissolve.",
            "Reflect on molecular interactions."
        ]
    },
    {
        "id": "proj_electrolysis",
        "title": "Electrolysis of Water",
        "subject": "Chemistry",
        "steps": [
            "Set up water with dissolved salt in a beaker.",
            "Insert two pencil leads as electrodes.",
            "Connect to battery.",
            "Observe gas bubbles at electrodes.",
            "Reflect on hydrogen/oxygen production."
        ]
    },

    # ---------------- Biology ----------------
    {
        "id": "proj_ecosystem_terrarium",
        "title": "Create a Closed Terrarium Ecosystem",
        "subject": "Biology",
        "steps": [
            "Plan components: soil, small plants/moss, stones, water.",
            "Explain energy flow and cycles inside.",
            "Build terrarium and observe for 2 weeks.",
            "Note imbalance and propose fixes.",
            "Share photos and reflection."
        ]
    },
    {
        "id": "proj_germination",
        "title": "Seed Germination Study",
        "subject": "Biology",
        "steps": [
            "Plant seeds in cotton and soil.",
            "Track sprouting time.",
            "Compare growth with/without sunlight.",
            "Water daily and record.",
            "Reflect on photosynthesis."
        ]
    },
    {
        "id": "proj_microscope_leaves",
        "title": "Microscopic Study of Leaves",
        "subject": "Biology",
        "steps": [
            "Collect leaves and prepare thin sections.",
            "Observe under microscope.",
            "Identify stomata and veins.",
            "Sketch structures.",
            "Reflect on adaptation."
        ]
    },
    {
        "id": "proj_dna_model",
        "title": "Build a DNA Model",
        "subject": "Biology",
        "steps": [
            "Research DNA double helix structure.",
            "Gather colored beads/straws.",
            "Assemble A-T, G-C pairs.",
            "Twist into helix.",
            "Reflect on replication."
        ]
    },
    {
        "id": "proj_invertebrates_survey",
        "title": "Invertebrates in Your Area",
        "subject": "Biology",
        "steps": [
            "Observe garden for ants, beetles, worms.",
            "Record diversity and count.",
            "Compare morning vs evening.",
            "Identify ecological role.",
            "Reflect on biodiversity importance."
        ]
    },
    {
        "id": "proj_heart_rate",
        "title": "Heart Rate and Exercise",
        "subject": "Biology",
        "steps": [
            "Measure resting pulse.",
            "Do exercise for 1 min.",
            "Measure pulse immediately after.",
            "Compare recovery time.",
            "Reflect on fitness."
        ]
    },
    {
        "id": "proj_leaf_color",
        "title": "Leaf Color and Photosynthesis",
        "subject": "Biology",
        "steps": [
            "Collect green, yellow, red leaves.",
            "Test starch with iodine after sunlight exposure.",
            "Compare color vs starch levels.",
            "Record observations.",
            "Reflect on chlorophyll role."
        ]
    },
    {
        "id": "proj_food_chain",
        "title": "Local Food Chain Study",
        "subject": "Biology",
        "steps": [
            "List producers, herbivores, carnivores nearby.",
            "Draw arrows showing energy transfer.",
            "Add humans in chain.",
            "Discuss effect of removing one species.",
            "Reflect on balance."
        ]
    },
    {
        "id": "proj_blood_group",
        "title": "Survey of Blood Groups",
        "subject": "Biology",
        "steps": [
            "Collect anonymous data from classmates.",
            "Make frequency chart of blood groups.",
            "Identify most common group.",
            "Compare with national averages.",
            "Reflect on genetics."
        ]
    },
    {
        "id": "proj_pollution_effects",
        "title": "Effects of Pollution on Plants",
        "subject": "Biology",
        "steps": [
            "Place plants near roadside and indoors.",
            "Observe leaf color, dust, growth.",
            "Record differences.",
            "Compare with clean-air plants.",
            "Reflect on air pollution impact."
        ]
    },

    # ---------------- Maths ----------------
    {
        "id": "proj_real_life_quadratics",
        "title": "Quadratics in Real Life",
        "subject": "Maths",
        "steps": [
            "Find a real problem involving a parabolic path.",
            "Model it as a quadratic function.",
            "Solve and interpret roots/vertex.",
            "Validate with estimates.",
            "Present model and limitations."
        ]
    },
    {
        "id": "proj_probability_game",
        "title": "Design a Probability Game",
        "subject": "Maths",
        "steps": [
            "Create a dice/card/spinner game.",
            "Predict winning chances.",
            "Play multiple times.",
            "Compare with theory.",
            "Reflect on fairness."
        ]
    },
    {
        "id": "proj_geometry_art",
        "title": "Create Geometry-based Art",
        "subject": "Maths",
        "steps": [
            "Use compass, protractor, ruler.",
            "Design patterns with circles, polygons.",
            "Identify symmetries.",
            "Measure angles and ratios.",
            "Reflect on math in art."
        ]
    },
    {
        "id": "proj_survey_statistics",
        "title": "Statistics from Daily Life",
        "subject": "Maths",
        "steps": [
            "Survey 20 people (favorite fruit, subject).",
            "Create frequency table.",
            "Draw bar graph or pie chart.",
            "Calculate mean, median, mode.",
            "Reflect on data patterns."
        ]
    },
    {
        "id": "proj_math_puzzle",
        "title": "Invent a Math Puzzle",
        "subject": "Maths",
        "steps": [
            "Design a puzzle using algebra/geometry.",
            "Test on friends/family.",
            "Record their solving time.",
            "Compare strategies.",
            "Reflect on puzzle design."
        ]
    },
    {
        "id": "proj_golden_ratio",
        "title": "Golden Ratio in Nature",
        "subject": "Maths",
        "steps": [
            "Measure spirals in shells/plants.",
            "Compare with golden ratio (1.618).",
            "Draw Fibonacci spirals.",
            "Photograph examples.",
            "Reflect on math in nature."
        ]
    },
    {
        "id": "proj_fractals",
        "title": "Draw a Fractal Pattern",
        "subject": "Maths",
        "steps": [
            "Research fractals like Koch snowflake.",
            "Draw iterative shapes.",
            "Count self-similar parts.",
            "Estimate perimeter/area.",
            "Reflect on infinite complexity."
        ]
    },
    {
        "id": "proj_optimal_path",
        "title": "Shortest Path Problem",
        "subject": "Maths",
        "steps": [
            "Draw a map of 5 points.",
            "Find shortest path manually.",
            "Test with different paths.",
            "Compare with graph theory.",
            "Reflect on applications."
        ]
    },
    {
        "id": "proj_measurement_errors",
        "title": "Experiment with Measurement Errors",
        "subject": "Maths",
        "steps": [
            "Measure a table using different rulers.",
            "Compare slight differences.",
            "Calculate average value.",
            "Discuss random/systematic errors.",
            "Reflect on precision."
        ]
    },
    {
        "id": "proj_game_theory",
        "title": "Game Theory in Daily Life",
        "subject": "Maths",
        "steps": [
            "Analyze rock-paper-scissors.",
            "Record outcomes in repeated trials.",
            "Predict strategies.",
            "Connect to Nash equilibrium.",
            "Reflect on decision-making."
        ]
    },

    # ---------------- English ----------------
    {
        "id": "proj_poetry_analysis",
        "title": "Analyze a Poem",
        "subject": "English",
        "steps": [
            "Choose a favorite poem.",
            "Identify rhyme scheme and imagery.",
            "Explain poet’s theme.",
            "Relate to personal experience.",
            "Reflect in 1-page report."
        ]
    },
    {
        "id": "proj_short_story",
        "title": "Write a Short Story",
        "subject": "English",
        "steps": [
            "Pick a theme (friendship, fear, hope).",
            "Write a 500-word short story.",
            "Add characters and conflict.",
            "Share with a friend for feedback.",
            "Reflect on storytelling."
        ]
    },
    {
        "id": "proj_newspaper_analysis",
        "title": "Newspaper Analysis",
        "subject": "English",
        "steps": [
            "Collect 3 front pages of newspapers.",
            "Analyze headline styles.",
            "Compare tone of writing.",
            "Identify persuasive language.",
            "Reflect on journalism."
        ]
    },
    {
        "id": "proj_script_play",
        "title": "Write a Play Script",
        "subject": "English",
        "steps": [
            "Pick a social issue.",
            "Write a 3-scene play.",
            "Include dialogues and stage notes.",
            "Perform with friends.",
            "Reflect on drama experience."
        ]
    },
    {
        "id": "proj_public_speech",
        "title": "Deliver a Speech",
        "subject": "English",
        "steps": [
            "Choose a topic of interest.",
            "Write a 3-minute speech.",
            "Practice aloud with mirror.",
            "Record video of delivery.",
            "Reflect on confidence."
        ]
    },
    {
        "id": "proj_letter_exchange",
        "title": "Letter Exchange Project",
        "subject": "English",
        "steps": [
            "Write a formal letter to a leader.",
            "Write an informal letter to a friend.",
            "Compare tone and structure.",
            "Get peer feedback.",
            "Reflect on communication."
        ]
    },
    {
        "id": "proj_interview",
        "title": "Conduct an Interview",
        "subject": "English",
        "steps": [
            "Choose a teacher or elder.",
            "Prepare 5 meaningful questions.",
            "Conduct and record interview.",
            "Summarize in 1-page report.",
            "Reflect on active listening."
        ]
    },
    {
        "id": "proj_debate",
        "title": "Organize a Debate",
        "subject": "English",
        "steps": [
            "Pick a debate topic relevant to your class.",
            "Form two teams and assign sides.",
            "Research arguments and counterarguments.",
            "Hold the debate and record key points.",
            "Reflect on what you learned from both sides."
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

    subject_list = ["Maths", "Physics", "Chemistry", "Biology", "English"]
    selected_project = st.selectbox(
        "Choose a project",
        PROJECT_TEMPLATES,
        format_func=lambda x: x["title"]
    )

    # Defensive: ensure selected_project is a dict
    if isinstance(selected_project, dict):
        subj = selected_project.get("subject", subject_list[0])
    else:
        subj = subject_list[0]
        for proj in PROJECT_TEMPLATES:
            if proj["title"] == selected_project:
                subj = proj.get("subject", subject_list[0])
                selected_project = proj
                break

    new_subject = st.selectbox(
        "Edit Subject",
        subject_list,
        index=subject_list.index(subj)
    )

    st.write(f"**Subject:** {new_subject}")
    st.write(f"**Project:** {selected_project['title']}")
    proj = selected_project  # so rest of the code works

    progress = load_project_progress()
    if proj["id"] not in progress:
        progress[proj["id"]] = {"completed": [False] * len(proj["steps"]), "notes": ""}

    # Steps checklist
    st.markdown("#### Steps")
    updated_completed = []
    for i, step in enumerate(proj["steps"]):
        checked = st.checkbox(step, value=progress[proj["id"]]["completed"][i], key=f"step_{proj['id']}_{i}")
        updated_completed.append(checked)

    # Notes field
    notes = st.text_area("Notes / Observations / Reflections", value=progress[proj["id"]].get("notes", ""), height=180, key=f"notes_{proj['id']}")

    # Upload evidence (optional)
    upload = st.file_uploader("Upload a photo or PDF (optional)", type=["png", "jpg", "jpeg", "pdf"], key=f"upload_{proj['id']}")
    if upload is not None:
        save_path = SUBMISSIONS_DIR / f"{proj['id']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{upload.name}"
        with open(save_path, "wb") as f:
            f.write(upload.read())
        st.success(f"Uploaded: {save_path.name}")

    # Save progress
    if st.button("Save Project Progress"):
        progress[proj["id"]]["completed"] = updated_completed
        progress[proj["id"]]["notes"] = notes
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

    st.title("🎓 Rancho-AI Personal Tutor")
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
