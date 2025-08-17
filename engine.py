import json, os, random, math
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sympy import sympify

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
QUESTION_FILE = os.path.join(DATA_DIR, "questions.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")

def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def _save_json(path: str, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_questions() -> List[Dict[str, Any]]:
    return _load_json(QUESTION_FILE, [])

def get_subjects(questions: List[Dict[str, Any]]) -> List[str]:
    return sorted(list({q["subject"] for q in questions if "subject" in q}))

def filter_questions(questions, subject: str, difficulty: int) -> List[Dict[str, Any]]:
    pool = [q for q in questions if q.get("subject", "").lower() == subject.lower() and abs(int(q.get("difficulty",1)) - difficulty) <= 1]
    if not pool:
        pool = [q for q in questions if q.get("subject", "").lower() == subject.lower()]
    return pool

def clamp(n, lo, hi): 
    return max(lo, min(hi, n))

def evaluate_answer(q: Dict[str, Any], user_input: str) -> Tuple[bool, str]:
    t = q.get("type", "mcq")
    if t == "mcq":
        # Allow either option text or index (1-based)
        ans = str(q.get("answer", "")).strip().lower()
        ui = user_input.strip().lower()
        options = q.get("options", [])
        if ui.isdigit() and options:
            idx = int(ui) - 1
            if 0 <= idx < len(options):
                ui = str(options[idx]).strip().lower()
        return (ui == ans, ans)
    elif t == "numeric":
        try:
            target = float(q.get("answer"))
        except Exception:
            target = float(sympify(str(q.get("answer"))))
        tol = float(q.get("tolerance", 0.01))
        try:
            ui_val = float(sympify(user_input))
        except Exception:
            try:
                ui_val = float(user_input)
            except Exception:
                return (False, str(q.get("answer")))
        ok = abs(ui_val - target) <= tol
        return (ok, str(q.get("answer")))
    else:  # text
        ui = user_input.strip().lower()
        ans = str(q.get("answer", "")).strip().lower()
        if ui == ans: 
            return (True, q.get("answer"))
        for alias in q.get("aliases", []):
            if ui == str(alias).strip().lower():
                return (True, q.get("answer"))
        return (False, q.get("answer"))

def load_progress() -> Dict[str, Any]:
    return _load_json(PROGRESS_FILE, {"users": {}})

def save_progress(progress: Dict[str, Any]):
    _save_json(PROGRESS_FILE, progress)

def record_event(user: str, subject: str, q: Dict[str, Any], correct: bool):
    progress = load_progress()
    users = progress.setdefault("users", {})
    u = users.setdefault(user, {"history": []})
    u["history"].append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "subject": subject,
        "topic": q.get("topic",""),
        "difficulty": int(q.get("difficulty",1)),
        "correct": bool(correct),
        "qid": q.get("id", None)
    })
    save_progress(progress)

def compute_report(user: str) -> Dict[str, Any]:
    progress = load_progress()
    u = progress.get("users", {}).get(user, {"history": []})
    hist = u.get("history", [])
    total = len(hist)
    correct = sum(1 for h in hist if h.get("correct"))
    acc = (correct/total*100) if total else 0.0
    # topic-wise accuracy
    per_topic = {}
    for h in hist:
        t = h.get("topic","")
        if t not in per_topic: per_topic[t] = {"total":0,"correct":0}
        per_topic[t]["total"] += 1
        per_topic[t]["correct"] += 1 if h.get("correct") else 0
    topic_stats = []
    for t, s in per_topic.items():
        if s["total"]==0: continue
        topic_stats.append({"topic": t, "attempts": s["total"], "accuracy": round(100*s["correct"]/s["total"],1)})
    topic_stats.sort(key=lambda x: x["accuracy"])
    weak = [t["topic"] for t in topic_stats[:3]]
    plan = []
    for w in weak:
        if not w: continue
        plan.append(f"Revise basics of {w}, practice 10 problems at difficulty 1–2, then reattempt quiz.")
    return {"total": total, "accuracy": round(acc,1), "topic_stats": topic_stats, "recommendations": plan}

class AdaptiveSelector:
    def __init__(self, start_difficulty: int = 2):
        self.d = start_difficulty

    def pick(self, questions: List[Dict[str, Any]], subject: str) -> Dict[str, Any]:
        pool = filter_questions(questions, subject, self.d)
        return random.choice(pool) if pool else {}

    def update(self, was_correct: bool):
        self.d = clamp(self.d + (1 if was_correct else -1), 1, 5)
