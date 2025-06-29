import sqlite3
import os
import csv

DATABASE_URL = "./helpbot.db"

def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()

    # Drop existing tables (for POC simplicity, in production you might migrate)
    c.execute("DROP TABLE IF EXISTS questions")
    c.execute("DROP TABLE IF EXISTS feedback")
    c.execute("DROP TABLE IF EXISTS query_log")

    # Create tables
    c.execute("""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            question TEXT,
            answer TEXT,
            article_link TEXT,
            tags TEXT,
            feedback INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            question_id INTEGER,
            feedback_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    c.execute("""
        CREATE TABLE query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            raw_query TEXT,
            matched_question_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Load data from CSV (assuming data.csv is in the workspace root)
    data_csv_path = "data.csv"
    if not os.path.exists(data_csv_path):
        print(f"Warning: {data_csv_path} not found. Cannot load initial data.")
    else:
        with open(data_csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    c.execute("""
                        INSERT INTO questions (id, question, answer, article_link, tags, feedback)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        int(row["id"]),
                        row["question"],
                        row["answer"],
                        row["article_link"],
                        row["tags"],
                        int(row["feedback"])
                    ))
                except ValueError as e:
                    print(f"Skipping row due to data error: {row} - {e}")

    conn.commit()
    conn.close()

def init_db_if_not_exists():
    if not os.path.exists(DATABASE_URL):
        print("Database not found. Initializing...")
        try:
            init_db()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Error during database initialization: {e}")
            # Depending on severity, you might want to sys.exit(1) here

def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    try:
        yield conn
    finally:
        conn.close() 