import json
import os
import random

QUESTIONS_DIR = "questions"
PROGRESS_FILE = "progress.json"
SUBJECTS = ["Maths", "Physics", "Chemistry", "Biology"]

def load_progress(username):
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Return user progress if available
                return data.get(username, {
                    "total_score": 0,
                    "progress": {sub: 0 for sub in SUBJECTS},
                    "questions_attended": []
                })
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    # Default progress
    return {
        "total_score": 0,
        "progress": {sub: 0 for sub in SUBJECTS},
        "questions_attended": []
    }

def save_progress(username, progress):
    data = {}
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    # Save under username
    data[username] = progress
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving progress: {e}")

def load_questions(subject, exam):
    filepath = os.path.join(QUESTIONS_DIR, f"{subject.lower()}.json")
    if not os.path.exists(filepath):
        print(f"No file found for {subject}. Please create '{filepath}'.")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Error reading questions file for {subject}.")
        return []

    return [q for q in questions if q.get("exam", "").upper() == exam.upper()]

def ask_questions(questions, num=5, attended=None):
    score = 0
    if attended is None:
        attended = []
    if not questions:
        print("No questions available for this exam.")
        return score, 0, attended

    selected = random.sample(questions, min(num, len(questions)))

    for i, q in enumerate(selected, start=1):
        print(f"\nQ{i}: {q.get('question', 'No question text')}")

        options = q.get("options", {})
        labels = list(options.keys())
        values = list(options.values())

        for j, option in enumerate(values, start=1):
            print(f"  {j}. {option}")

        try:
            ans = int(input("Your answer (1-4): "))
            if 1 <= ans <= 4:
                chosen_label = labels[ans - 1]
                if chosen_label == q.get("answer"):
                    print("✅ Correct!")
                    score += 1
                else:
                    print(f"❌ Wrong! Correct answer: {options.get(q.get('answer'), 'Unknown')}")
            else:
                print("Invalid option, moving on...")
        except Exception:
            print("Invalid input, moving on...")

        # Track attended question by ID if available, else by question text
        attended.append(q.get("id", q.get("question", "")))
    return score, len(selected), attended

def main():
    # Ask for username
    username = input("👋 Enter your name: ").strip()
    if not username:
        username = "Guest"

    progress = load_progress(username)

    while True:
        print(f"\n👋 Welcome back, {username}!")
        print(f"📈 Total Score: {progress['total_score']}")
        print(f"✅ Progress: {progress['progress']}")
        print(f"📝 Questions Attended: {len(progress.get('questions_attended', []))}")

        print("\nChoose a subject:")
        for i, sub in enumerate(SUBJECTS, start=1):
            print(f"{i}. {sub}")
        print("0. Exit")

        try:
            choice = int(input("Enter choice: "))
        except Exception:
            print("Invalid input, try again.")
            continue

        if choice == 0:
            print("Goodbye! Keep studying 🚀")
            save_progress(username, progress)
            break
        elif 1 <= choice <= len(SUBJECTS):
            subject = SUBJECTS[choice - 1]
        else:
            print("Invalid choice, try again.")
            continue

        exam = input("Preparing for JEE or NEET? ").strip().upper()
        if exam not in ["JEE", "NEET"]:
            print("Invalid exam choice.")
            continue

        questions = load_questions(subject, exam)
        if not questions:
            print(f"No questions found for {subject} ({exam}).")
            continue

        print(f"\n📚 Starting {subject} ({exam}) quiz...")
        score, total, attended = ask_questions(
            questions,
            attended=progress.get("questions_attended", [])
        )
        print(f"\n🎯 You scored {score}/{total}")

        progress["total_score"] += score
        progress["progress"][subject] += score
        progress["questions_attended"] = attended
        save_progress(username, progress)

if __name__ == "__main__":
    main()
