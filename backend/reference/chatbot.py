import sqlite3
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import re
import nltk
from rapidfuzz import fuzz
import random

nltk.download("stopwords")
stop_words = set(stopwords.words("english"))
stemmer = PorterStemmer()


GREETING_KEYWORDS = {"hi", "hello", "hey", "greetings", "good morning", "good evening"}
GREETINGS = [
    "👋 Hey there!", "Hello! 😊", "Hi, great to see you!", "Greetings!", "Howdy!", "Hey! 👋",
    "Hiya!", "Good to see you!", "Hello, sunshine! ☀️", "Yo!", "What's up?", "Hi there!",
    "Welcome aboard!", "Ahoy!", "Hi friend! 👋", "Nice to have you here!", "Hola!", "Ciao!",
    "Salutations!", "Hello, world!", "Peace be upon you!", "Hi genius! 💡", "Sup?", "Hello, rockstar! 🎸",
    "Wassup!", "Namaste 🙏", "Hello explorer!", "Welcome, legend!", "Hi, how's it going?", "👋 Howdy, partner!",
    "Hi, let's get started!", "Hey superstar!", "Hello hero! 🦸", "Hi, need assistance?", "Hi champion!"
]
HELP_KEYWORDS = {"help", "need help", "assist", "support", "can you help", "i need help"}
HELP_RESPONSES = [
    "🤖 I’m here to help! Here are some common things people ask:",
    "👋 Need assistance? You're in the right place! Here are a few popular questions:",
    "🛠️ I'm on it! Here's what others often ask:",
    "🙋 Sure thing! Check out these frequently asked questions:",
    "💬 Let's solve this together! Here's a quick list of common queries:",
    "📘 Here’s a guide to get you started — people often ask these things:",
    "🧠 I'm your go-to brain! These might help you out:",
    "✨ Ready to help! Here’s what others have needed help with:",
    "🧐 Here's a quick pick of common questions — maybe yours is here too!",
    "📌 Let's figure this out. Meanwhile, check out these top questions:"
]


FILLER_PHRASES = [
    "i need help with", "i need help on", "i need help", "please help", "can you help me with",
    "how do i", "how to", "i want to", "tell me how to", "what is the way to", "help me"
]

def clean_input(text):
    text = text.lower().strip()
    for phrase in FILLER_PHRASES:
        text = text.replace(phrase, "")
    return text.strip()

def preprocess(text):
    text = clean_input(text)
    words = re.findall(r'\b\w+\b', text.lower())
    return [stemmer.stem(w) for w in words if w not in stop_words]

# def is_greeting(text):
#     return any(word in text.lower() for word in GREETING_KEYWORDS)

# def is_help_request(text):
#     return any(word in text.lower() for word in HELP_KEYWORDS)

def is_greeting(text):
    text = text.lower()
    for keyword in GREETING_KEYWORDS:
        if re.search(rf'\b{re.escape(keyword)}\b', text):
            return True
    return False

def is_help_request(text):
    text = text.lower()
    for phrase in HELP_KEYWORDS:
        if re.search(rf'\b{re.escape(phrase)}\b', text):
            return True
    return False


def match_questions(user_input, questions):
    user_input = user_input.strip().lower()

    # Handle greetings
    if is_greeting(user_input):
        return {
            "type": "greeting",
            "message": f"{random.choice(GREETINGS)} How can I help you today?",
            "results": sorted(questions, key=lambda q: -q["feedback"])[:5]
        }

    # Handle help phrases
    if is_help_request(user_input):
        return {
            "type": "help",
            "message": random.choice(HELP_RESPONSES), 
            "results": sorted(questions, key=lambda q: -q["feedback"])[:5]
        }

    # Normal fuzzy matching
    input_tokens = preprocess(user_input)
    matches = []
    for row in questions:
        question_tokens = preprocess(row["question"] + " " + row["tags"])
        score = fuzz.token_set_ratio(" ".join(input_tokens), " ".join(question_tokens))
        if score >= 50:
            matches.append((score, row["feedback"], row))

    matches.sort(key=lambda x: (-x[0], -x[1]))
    return {
        "type": "match",
        "results": [row for _, _, row in matches]
    }


class HelpBot:
    def __init__(self, db_path="helpbot.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def get_top_questions(self, limit=5):
        q = self.conn.cursor()
        q.execute("""
            SELECT questions.*, COUNT(query_log.id) AS query_count
            FROM questions
            LEFT JOIN query_log ON questions.id = query_log.matched_question_id
            GROUP BY questions.id
            ORDER BY query_count DESC, feedback DESC
            LIMIT ?
        """, (limit,))
        return q.fetchall()

    def suggest_questions(self, user_input):
        q = self.conn.cursor()
        q.execute("SELECT * FROM questions")
        rows = q.fetchall()
        return match_questions(user_input, rows)

    def get_answer(self, question_id):
        q = self.conn.cursor()
        q.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = q.fetchone()
        if row:
            return f"{row['answer']}\nMore info: <a href='{row['article_link']}'>{row['article_link']}</a>"
        return "No answer found."

    def log_query(self, user_name, raw_query, matched_question_id):
        q = self.conn.cursor()
        q.execute("""
            INSERT INTO query_log (user_name, raw_query, matched_question_id)
            VALUES (?, ?, ?)
        """, (user_name, raw_query, matched_question_id))
        self.conn.commit()

    def save_feedback(self, user_name, question_id, score):
        q = self.conn.cursor()
        q.execute("""
            INSERT INTO feedback (user_name, question_id, feedback_score)
            VALUES (?, ?, ?)
        """, (user_name, question_id, score))
        self.conn.commit()