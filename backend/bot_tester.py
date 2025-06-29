# HelpBot Usage Examples & Implementation Guide

from reference.advance_test_bot_v1 import AdvancedHelpBot, BotResponse, ResponseType
from datetime import datetime

# Example 1: Basic Usage
def basic_usage_example():
    """Basic implementation example"""
    print("=== Basic Usage Example ===")
    
    # Initialize bot
    bot = AdvancedHelpBot(db_path="example_bot.db")
    
    # Sample questions to populate the database
    sample_questions = [
        {
            "question": "How do I reset my password?",
            "answer": "To reset your password: 1. Go to login page 2. Click 'Forgot Password' 3. Enter your email 4. Check your email for reset link",
            "tags": "password reset login authentication",
            "category": "account",
            "article_link": "https://help.example.com/password-reset"
        },
        {
            "question": "How do I cancel my subscription?",
            "answer": "To cancel: 1. Go to Account Settings 2. Click 'Billing' 3. Select 'Cancel Subscription' 4. Confirm cancellation",
            "tags": "cancel subscription billing account",
            "category": "billing",
            "article_link": "https://help.example.com/cancel-subscription"
        },
        {
            "question": "How do I contact customer support?",
            "answer": "You can contact us via: 1. Live chat (9AM-6PM) 2. Email: support@example.com 3. Phone: 1-800-123-4567",
            "tags": "contact support help customer service",
            "category": "support",
            "article_link": "https://help.example.com/contact"
        }
    ]
    
    # Add sample questions (you would typically do this once during setup)
    cursor = bot.conn.cursor()
    for q in sample_questions:
        cursor.execute("""
            INSERT OR IGNORE INTO questions (question, answer, tags, category, article_link)
            VALUES (?, ?, ?, ?, ?)
        """, (q["question"], q["answer"], q["tags"], q["category"], q["article_link"]))
    bot.conn.commit()
    
    # Test various user inputs
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

basic_usage_example()