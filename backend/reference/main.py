from chatbot import HelpBot

def run_bot():
    bot = HelpBot()
    user_name = input("👋 Welcome! Please enter your name: ").strip()

    # Show top questions
    top_questions = bot.get_top_questions()
    if top_questions:
        print("\n🔥 Most common questions:")
        for i, row in enumerate(top_questions, 1):
            print(f"{i}. {row['question']}")

    while True:
        # First ask if user wants to pick from top questions:
        choice = input("\nSelect a question number from above, or press Enter to type your query (or 'exit'): ").strip().lower()

        if choice == 'exit':
            print("Goodbye!")
            break

        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(top_questions):
                selected = top_questions[num - 1]
                print("\n" + bot.get_answer(selected["id"]))
                bot.log_query(user_name, selected["question"], selected["id"])

                # Ask for feedback
                while True:
                    fb = input("📝 Rate this answer (1–5) or press Enter to skip: ").strip()
                    if fb == '':
                        break
                    elif fb in {'1','2','3','4','5'}:
                        bot.save_feedback(user_name, selected["id"], int(fb))
                        print("✅ Thanks for your feedback!")
                        break
                    else:
                        print("Invalid input.")
                continue  # Go back to asking for next question

            else:
                print(f"Please select a number between 1 and {len(top_questions)}.")
                continue

        # If not a number, treat as query
        user_query = choice
        if not user_query:
            print("Please enter a question number or your query.")
            continue

        suggestions = bot.suggest_questions(user_query)
        if not suggestions:
            print("Sorry, no matches. Try keywords like 'password', 'email', 'invite', 'billing'.")
            continue

        page_size = 5
        index = 0

        while True:
            current = suggestions[index:index+page_size]
            if not current:
                print("No more results. Contact support.")
                break

            print("\nSuggested Questions:")
            for i, row in enumerate(current, 1):
                print(f"{i}. {row['question']}")

            choice2 = input("Select 1–5, type 'more', '0' for support, or 'exit': ").strip().lower()
            if choice2 == 'more':
                index += page_size
                continue
            elif choice2 == '0':
                print("📞 Contact support: https://example.com/contact")
                break
            elif choice2 == 'exit':
                print("Goodbye!")
                return
            elif choice2.isdigit():
                num2 = int(choice2)
                if 1 <= num2 <= len(current):
                    selected = current[num2 - 1]
                    print("\n" + bot.get_answer(selected["id"]))
                    bot.log_query(user_name, user_query, selected["id"])
                    # Ask for feedback
                    while True:
                        fb = input("📝 Rate this answer (1–5) or press Enter to skip: ").strip()
                        if fb == '':
                            break
                        elif fb in {'1','2','3','4','5'}:
                            bot.save_feedback(user_name, selected["id"], int(fb))
                            print("✅ Thanks for your feedback!")
                            break
                        else:
                            print("Invalid input.")
                    break
                else:
                    print("Invalid choice.")
            else:
                print("Invalid input.")

if __name__ == "__main__":
    run_bot()
