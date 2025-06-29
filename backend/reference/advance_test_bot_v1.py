import sqlite3
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
import re
import nltk
from rapidfuzz import fuzz, process
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
# import json
# import requests
from collections import defaultdict, Counter

# Download required NLTK data
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("wordnet", quiet=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseType(Enum):
    GREETING = "greeting"
    HELP = "help"
    MATCH = "match"
    NO_MATCH = "no_match"
    ERROR = "error"
    PAGINATION = "pagination"
    SUGGESTION = "suggestion"
    ESCALATION = "escalation"
    CONTACT_SUPPORT = "contact_support"

class ErrorType(Enum):
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    GENERAL_ERROR = "general_error"

@dataclass
class BotResponse:
    type: ResponseType
    message: str
    results: List[Dict] = None
    error: Optional[str] = None
    pagination: Optional[Dict] = None
    suggestions: List[str] = None
    escalation_info: Optional[Dict] = None
    confidence_score: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class AdvancedHelpBot:
    def __init__(self, db_path="helpbot.db"):
        self.db_path = db_path
        self.conn = None
        self.stop_words = set(stopwords.words("english"))
        self.stemmer = PorterStemmer()
        self.user_sessions = {}
        self.rate_limits = defaultdict(list)
        
        # Enhanced keyword sets
        self.greeting_keywords = {
            "hi", "hello", "hey", "greetings", "good morning", "good evening",
            "howdy", "sup", "yo", "hiya", "bonjour", "hola", "ciao"
        }
        
        self.help_keywords = {
            "help", "need help", "assist", "support", "can you help",
            "i need help", "assistance", "guide", "tutorial", "how to"
        }
        
        self.escalation_keywords = {
            "speak to human", "human agent", "customer service", "live chat",
            "representative", "operator", "support team", "contact support",
            "escalate", "manager", "supervisor"
        }
        
        self.negative_feedback_keywords = {
            "not helpful", "doesn't work", "wrong answer", "useless",
            "bad", "terrible", "awful", "disappointed", "frustrated"
        }
        
        # Response templates
        self.greetings = [
            "👋 Hey there! I'm here to help you find answers quickly.",
            "Hello! 😊 What can I assist you with today?",
            "Hi! I'm your AI assistant. How can I help?",
            "Greetings! Ready to solve your questions together!",
            "Hey! 👋 Let's get you the help you need."
        ]
        
        self.help_responses = [
            "🤖 I'm here to help! Here are some ways I can assist:",
            "👋 Need assistance? Here are popular topics:",
            "🛠️ I can help with various topics. Here are some options:",
            "🙋 Let's find what you need! Here are common questions:"
        ]
        
        self.no_match_responses = [
            "🤔 I couldn't find exact matches, but here are some related topics:",
            "🔍 No direct matches found. These might be helpful:",
            "💡 Let me suggest some alternatives that might help:",
            "🎯 I didn't find that specific topic, but check these out:"
        ]
        
        self.error_responses = {
            ErrorType.DATABASE_ERROR: "⚠️ I'm having trouble accessing the knowledge base. Please try again in a moment.",
            ErrorType.NETWORK_ERROR: "🌐 Network issue detected. Please check your connection and try again.",
            ErrorType.VALIDATION_ERROR: "❌ I didn't understand that input. Could you rephrase your question?",
            ErrorType.RATE_LIMIT_ERROR: "⏰ You're asking questions very quickly! Please wait a moment before trying again.",
            ErrorType.GENERAL_ERROR: "🛠️ Something went wrong on my end. Let me try to help you anyway."
        }
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection with error handling"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Enhanced tables with new fields
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                tags TEXT,
                category TEXT,
                difficulty_level INTEGER DEFAULT 1,
                article_link TEXT,
                feedback REAL DEFAULT 0.0,
                view_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                session_id TEXT,
                raw_query TEXT,
                processed_query TEXT,
                matched_question_id INTEGER,
                confidence_score REAL,
                response_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (matched_question_id) REFERENCES questions (id)
            );
            
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                session_id TEXT,
                question_id INTEGER,
                feedback_score INTEGER,
                feedback_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions (id)
            );
            
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_name TEXT,
                last_query TEXT,
                last_results TEXT,
                current_page INTEGER DEFAULT 1,
                total_pages INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_name TEXT,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
    
    def _check_rate_limit(self, user_identifier: str, limit: int = 10, window: int = 60) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        # Clean old entries
        self.rate_limits[user_identifier] = [
            timestamp for timestamp in self.rate_limits[user_identifier]
            if timestamp > window_start
        ]
        
        # Check current count
        if len(self.rate_limits[user_identifier]) >= limit:
            return False
        
        # Add current request
        self.rate_limits[user_identifier].append(now)
        return True
    
    def _validate_input(self, text: str) -> bool:
        """Validate user input"""
        if not text or not text.strip():
            return False
        if len(text) > 1000:  # Too long
            return False
        if len(text.split()) > 100:  # Too many words
            return False
        return True
    
    def preprocess_text(self, text: str) -> List[str]:
        """Enhanced text preprocessing with NLP"""
        if not text:
            return []
        
        # Clean and normalize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove filler phrases
        filler_phrases = [
            "i need help with", "i need help on", "please help", "can you help me with",
            "how do i", "how to", "i want to", "tell me how to", "what is the way to"
        ]
        
        for phrase in filler_phrases:
            text = text.replace(phrase, "")
        
        # Tokenize and get POS tags
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        
        # Keep important words (nouns, verbs, adjectives)
        important_pos = {'NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'JJ', 'JJR', 'JJS'}
        important_words = [word for word, pos in pos_tags if pos in important_pos or len(word) > 3]
        
        # Filter stopwords and stem
        processed = [
            self.stemmer.stem(word) for word in important_words
            if word not in self.stop_words and len(word) > 2
        ]
        
        return processed
    
    def _detect_intent(self, text: str) -> str:
        """Detect user intent from text"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in self.greeting_keywords):
            return "greeting"
        elif any(keyword in text_lower for keyword in self.escalation_keywords):
            return "escalation"
        elif any(keyword in text_lower for keyword in self.help_keywords):
            return "help"
        elif any(keyword in text_lower for keyword in self.negative_feedback_keywords):
            return "negative_feedback"
        else:
            return "question"
    
    def _fuzzy_match_questions(self, user_input: str, questions: List[Dict]) -> List[Tuple[float, Dict]]:
        """Enhanced fuzzy matching with multiple algorithms"""
        input_tokens = self.preprocess_text(user_input)
        input_text = " ".join(input_tokens)
        
        matches = []
        
        for question in questions:
            question_tokens = self.preprocess_text(f"{question['question']} {question.get('tags', '')}")
            question_text = " ".join(question_tokens)
            
            # Multiple scoring methods
            token_set_score = fuzz.token_set_ratio(input_text, question_text)
            token_sort_score = fuzz.token_sort_ratio(input_text, question_text)
            partial_score = fuzz.partial_ratio(user_input.lower(), question['question'].lower())
            
            # Weighted average
            final_score = (token_set_score * 0.4 + token_sort_score * 0.4 + partial_score * 0.2)
            
            # Boost score for exact word matches
            common_words = set(input_tokens) & set(question_tokens)
            if common_words:
                boost = min(len(common_words) * 5, 20)
                final_score += boost
            
            if final_score >= 40:  # Lower threshold for more matches
                matches.append((final_score, question))
        
        return sorted(matches, key=lambda x: (-x[0], -x[1].get('feedback', 0), -x[1].get('view_count', 0)))
    
    def _get_suggestions_based_on_history(self, session_id: str) -> List[str]:
        """Get suggestions based on user's query history"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT q.question, q.category, COUNT(*) as freq
                FROM query_log ql
                JOIN questions q ON ql.matched_question_id = q.id
                WHERE ql.session_id = ? AND ql.timestamp > datetime('now', '-1 day')
                GROUP BY q.category
                ORDER BY freq DESC
                LIMIT 3
            """, (session_id,))
            
            results = cursor.fetchall()
            suggestions = []
            
            for row in results:
                cursor.execute("""
                    SELECT question FROM questions 
                    WHERE category = ? AND id NOT IN (
                        SELECT matched_question_id FROM query_log 
                        WHERE session_id = ? AND matched_question_id IS NOT NULL
                    )
                    ORDER BY feedback DESC, view_count DESC
                    LIMIT 2
                """, (row['category'], session_id))
                
                category_suggestions = cursor.fetchall()
                suggestions.extend([s['question'] for s in category_suggestions])
            
            return suggestions[:5]
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def _paginate_results(self, results: List[Dict], page: int = 1, per_page: int = 5) -> Dict:
        """Paginate results with metadata"""
        total_items = len(results)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return {
            "items": results[start_idx:end_idx],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "per_page": per_page,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def _create_escalation(self, session_id: str, user_name: str, reason: str) -> Dict:
        """Create escalation request"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO escalations (session_id, user_name, reason)
                VALUES (?, ?, ?)
            """, (session_id, user_name, reason))
            self.conn.commit()
            
            escalation_id = cursor.lastrowid
            
            return {
                "escalation_id": escalation_id,
                "status": "pending",
                "estimated_wait_time": "5-10 minutes",
                "contact_options": self._get_contact_options()
            }
        except Exception as e:
            logger.error(f"Error creating escalation: {e}")
            return {"error": "Failed to create escalation request"}
    
    def _get_contact_options(self) -> Dict:
        """Get available contact support options"""
        return {
            "live_chat": {
                "available": True,
                "platform": "Intercom",
                "url": "https://widget.intercom.io/widget/your_app_id",
                "description": "Chat with our support team"
            },
            "email": {
                "available": True,
                "address": "support@yourcompany.com",
                "expected_response": "Within 24 hours"
            },
            "phone": {
                "available": True,
                "number": "+1-800-123-4567",
                "hours": "Mon-Fri 9AM-6PM EST"
            },
            "ticket_system": {
                "available": True,
                "platform": "Zendesk",
                "url": "https://yourcompany.zendesk.com/hc/en-us/requests/new",
                "description": "Submit a support ticket"
            }
        }
    
    def process_query(self, user_input: str, user_name: str = "anonymous", 
                     session_id: str = None, page: int = 1) -> BotResponse:
        """Main query processing function with comprehensive error handling"""
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"{user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Rate limiting
            if not self._check_rate_limit(f"{user_name}_{session_id}"):
                return BotResponse(
                    type=ResponseType.ERROR,
                    message=self.error_responses[ErrorType.RATE_LIMIT_ERROR],
                    error="rate_limit_exceeded"
                )
            
            # Input validation
            if not self._validate_input(user_input):
                return BotResponse(
                    type=ResponseType.ERROR,
                    message=self.error_responses[ErrorType.VALIDATION_ERROR],
                    error="invalid_input"
                )
            
            # Detect intent
            intent = self._detect_intent(user_input)
            
            # Handle different intents
            if intent == "greeting":
                return self._handle_greeting(session_id)
            elif intent == "escalation":
                return self._handle_escalation(user_input, user_name, session_id)
            elif intent == "help":
                return self._handle_help_request(session_id, page)
            else:
                return self._handle_question(user_input, user_name, session_id, page)
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return BotResponse(
                type=ResponseType.ERROR,
                message=self.error_responses[ErrorType.DATABASE_ERROR],
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return BotResponse(
                type=ResponseType.ERROR,
                message=self.error_responses[ErrorType.GENERAL_ERROR],
                error=str(e)
            )
    
    def _handle_greeting(self, session_id: str) -> BotResponse:
        """Handle greeting intent"""
        top_questions = self._get_top_questions(limit=5)
        suggestions = self._get_suggestions_based_on_history(session_id)
        
        return BotResponse(
            type=ResponseType.GREETING,
            message=random.choice(self.greetings),
            results=top_questions,
            suggestions=suggestions,
            confidence_score=1.0
        )
    
    def _handle_help_request(self, session_id: str, page: int) -> BotResponse:
        """Handle help request intent"""
        top_questions = self._get_top_questions(limit=20)
        paginated = self._paginate_results(top_questions, page, per_page=5)
        suggestions = self._get_suggestions_based_on_history(session_id)
        
        return BotResponse(
            type=ResponseType.HELP,
            message=random.choice(self.help_responses),
            results=paginated["items"],
            pagination=paginated["pagination"],
            suggestions=suggestions,
            confidence_score=0.9
        )
    
    def _handle_escalation(self, user_input: str, user_name: str, session_id: str) -> BotResponse:
        """Handle escalation to human support"""
        escalation_info = self._create_escalation(session_id, user_name, user_input)
        
        return BotResponse(
            type=ResponseType.ESCALATION,
            message="I'll connect you with human support. Here are your options:",
            escalation_info=escalation_info,
            confidence_score=1.0
        )
    
    def _handle_question(self, user_input: str, user_name: str, 
                        session_id: str, page: int) -> BotResponse:
        """Handle regular question intent"""
        # Get all questions from database
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM questions ORDER BY feedback DESC, view_count DESC")
        questions = [dict(row) for row in cursor.fetchall()]
        
        # Perform fuzzy matching
        matches = self._fuzzy_match_questions(user_input, questions)
        
        if not matches:
            # No matches found
            top_questions = self._get_top_questions(limit=5)
            suggestions = self._get_suggestions_based_on_history(session_id)
            
            return BotResponse(
                type=ResponseType.NO_MATCH,
                message=random.choice(self.no_match_responses),
                results=top_questions,
                suggestions=suggestions,
                confidence_score=0.0
            )
        
        # Extract matched questions and paginate
        matched_questions = [match[1] for match in matches]
        confidence_score = matches[0][0] / 100.0  # Convert to 0-1 scale
        
        paginated = self._paginate_results(matched_questions, page, per_page=5)
        
        # Log the query
        self._log_query(user_name, session_id, user_input, matched_questions[0]['id'], confidence_score)
        
        # Update view count for top match
        self._update_view_count(matched_questions[0]['id'])
        
        return BotResponse(
            type=ResponseType.MATCH,
            message=f"I found {len(matched_questions)} relevant results:",
            results=paginated["items"],
            pagination=paginated["pagination"],
            confidence_score=confidence_score
        )
    
    def _get_top_questions(self, limit: int = 5) -> List[Dict]:
        """Get top questions by popularity and feedback"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT q.*, COALESCE(COUNT(ql.id), 0) as query_count
                FROM questions q
                LEFT JOIN query_log ql ON q.id = ql.matched_question_id
                GROUP BY q.id
                ORDER BY query_count DESC, q.feedback DESC, q.view_count DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting top questions: {e}")
            return []
    
    def _log_query(self, user_name: str, session_id: str, raw_query: str, 
                  matched_question_id: int, confidence_score: float):
        """Log user query with enhanced information"""
        try:
            processed_query = " ".join(self.preprocess_text(raw_query))
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO query_log (user_name, session_id, raw_query, processed_query, 
                                     matched_question_id, confidence_score, response_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_name, session_id, raw_query, processed_query, 
                  matched_question_id, confidence_score, "match"))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error logging query: {e}")
    
    def _update_view_count(self, question_id: int):
        """Update view count for a question"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE questions SET view_count = view_count + 1 
                WHERE id = ?
            """, (question_id,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error updating view count: {e}")
    
    def get_question_details(self, question_id: int) -> Dict:
        """Get detailed information about a specific question"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()
            
            if row:
                question = dict(row)
                # Add formatted answer with link
                if question.get('article_link'):
                    question['formatted_answer'] = f"{question['answer']}\n\n📖 More info: {question['article_link']}"
                else:
                    question['formatted_answer'] = question['answer']
                
                return question
            return {}
        except Exception as e:
            logger.error(f"Error getting question details: {e}")
            return {}
    
    def save_feedback(self, user_name: str, session_id: str, question_id: int, 
                     feedback_score: int, feedback_text: str = "") -> bool:
        """Save user feedback with enhanced tracking"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (user_name, session_id, question_id, 
                                    feedback_score, feedback_text)
                VALUES (?, ?, ?, ?, ?)
            """, (user_name, session_id, question_id, feedback_score, feedback_text))
            
            # Update question's average feedback
            cursor.execute("""
                UPDATE questions 
                SET feedback = (
                    SELECT AVG(feedback_score) 
                    FROM feedback 
                    WHERE question_id = ?
                )
                WHERE id = ?
            """, (question_id, question_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False
    
    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics data for the chatbot"""
        try:
            cursor = self.conn.cursor()
            
            # Query statistics
            cursor.execute("""
                SELECT COUNT(*) as total_queries,
                       AVG(confidence_score) as avg_confidence,
                       COUNT(DISTINCT session_id) as unique_sessions
                FROM query_log 
                WHERE timestamp > datetime('now', '-{} days')
            """.format(days))
            query_stats = dict(cursor.fetchone())
            
            # Top questions
            cursor.execute("""
                SELECT q.question, COUNT(ql.id) as query_count
                FROM questions q
                JOIN query_log ql ON q.id = ql.matched_question_id
                WHERE ql.timestamp > datetime('now', '-{} days')
                GROUP BY q.id
                ORDER BY query_count DESC
                LIMIT 10
            """.format(days))
            top_questions = [dict(row) for row in cursor.fetchall()]
            
            # Feedback statistics
            cursor.execute("""
                SELECT AVG(feedback_score) as avg_feedback,
                       COUNT(*) as total_feedback
                FROM feedback 
                WHERE timestamp > datetime('now', '-{} days')
            """.format(days))
            feedback_stats = dict(cursor.fetchone())
            
            return {
                "query_statistics": query_stats,
                "top_questions": top_questions,
                "feedback_statistics": feedback_stats,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
    
    def external_support_integration(self, platform: str, user_data: Dict) -> Dict:
        """Integrate with external support platforms"""
        
        integrations = {
            "intercom": self._integrate_intercom,
            "zendesk": self._integrate_zendesk,
            "freshdesk": self._integrate_freshdesk,
            "crisp": self._integrate_crisp
        }
        
        if platform.lower() in integrations:
            return integrations[platform.lower()](user_data)
        else:
            return {"error": f"Platform {platform} not supported"}
    
    def _integrate_intercom(self, user_data: Dict) -> Dict:
        """Integrate with Intercom for live chat"""
        return {
            "platform": "intercom",
            "widget_url": "https://widget.intercom.io/widget/your_app_id",
            "config": {
                "app_id": "your_app_id",
                "user_id": user_data.get("user_id"),
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "created_at": int(datetime.now().timestamp())
            },
            "instructions": "Add the Intercom widget to your webpage"
        }
    
    def _integrate_zendesk(self, user_data: Dict) -> Dict:
        """Integrate with Zendesk for ticket creation"""
        return {
            "platform": "zendesk",
            "ticket_url": "https://yourcompany.zendesk.com/api/v2/tickets.json",
            "config": {
                "subdomain": "yourcompany",
                "username": "your_username",
                "token": "your_api_token"
            },
            "instructions": "Use Zendesk API to create tickets"
        }
    
    def _integrate_freshdesk(self, user_data: Dict) -> Dict:
        """Integrate with Freshdesk"""
        return {
            "platform": "freshdesk",
            "api_url": "https://yourcompany.freshdesk.com/api/v2/tickets",
            "config": {
                "domain": "yourcompany",
                "api_key": "your_api_key"
            },
            "instructions": "Use Freshdesk API for ticket management"
        }
    
    def _integrate_crisp(self, user_data: Dict) -> Dict:
        """Integrate with Crisp chat"""
        return {
            "platform": "crisp",
            "widget_url": "https://client.crisp.chat/l.js",
            "config": {
                "website_id": "your_website_id",
                "user_nickname": user_data.get("name"),
                "user_email": user_data.get("email")
            },
            "instructions": "Add Crisp chat widget to your webpage"
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

# Usage example and testing functions
def demo_usage():
    """Demonstrate how to use the advanced helpbot"""
    # Test various user inputs
    bot = AdvancedHelpBot('./helpbot.db')

    test_inputs = [
        "Hello!",
        "I need help with my password",
        "How can I cancel?",
        "I want to speak to a human",
        "This is frustrating, nothing works",
        "Show me more options"
    ]
    
    session_id = "demo_session_001"
    user_name = "demo_user"
    
    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        response = bot.process_query(user_input, user_name, session_id)
        
        print(f"🤖 Bot ({response.type.value}): {response.message}")
        print(f"📊 Confidence: {response.confidence_score:.2f}")
        
        if response.results:
            print(f"📋 Results ({len(response.results)} found):")
            for i, result in enumerate(response.results[:2], 1):
                print(f"  {i}. {result['question']}")
        
        if response.suggestions:
            print(f"💡 Suggestions: {', '.join(response.suggestions[:3])}")
        
        if response.escalation_info:
            print(f"📞 Escalation options available")
        
        print("-" * 60)
    
    bot.close()


if __name__ == "__main__":
    # demo_usage()
    pass
        