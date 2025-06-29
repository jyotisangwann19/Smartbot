import React, { useState, useEffect, useRef, use } from "react";
import { suggestQuestions, getAnswer, greetings } from "../apiCaller/api";

import { SendHorizontal } from "lucide-react";

interface Message {
  text: string;
  sender: "user" | "bot";
  isSuggestion?: boolean;
  suggestions?: any[];
}

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ChatModal: React.FC<ChatModalProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleGreetings = async () => {
    const response = await greetings("Test User ");
    return response;
  };

  useEffect(() => {
    async function greet(user_name: string | null) {
      if (messages.length < 1) {
        try {
          const response_data = await handleGreetings();
          console.log("Greeting response:", response_data);

          setMessages((prevMsg) => [
            {
              text: "Hii, I am Test User ",
              sender: "user",
            },
            {
              text: response_data.greetings,
              sender: "bot",
              isSuggestion: true,
              suggestions: response_data.questions,
            },
          ]);
        } catch (error) {
          console.error("Failed to get greeting:", error);
        }
      }
    }

    if (isOpen) {
      void greet("Test User ");
    }

    return () => {
      void greet(null);
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async () => {
    if (input.trim()) {
      const newUserMessage: Message = { text: input, sender: "user" };
      setMessages((prevMessages) => [...prevMessages, newUserMessage]);
      setInput("");

      try {
        const response = await suggestQuestions(input);

        const suggestions = response.data;

        if (suggestions && suggestions.suggestions.length > 0) {
          const botResponse: Message = {
            text: suggestions.message,
            sender: "bot",
            isSuggestion: true,
            suggestions: suggestions.suggestions,
          };
          setMessages((prevMessages) => [...prevMessages, botResponse]);
        } else {
          const botResponse: Message = {
            text: suggestions.message,
            sender: "bot",
          };
          setMessages((prevMessages) => [...prevMessages, botResponse]);
        }
      } catch (error) {
        console.error("Error sending message:", error);
        const errorMessage: Message = {
          text: "Sorry, But this is out of my scope, Try contact the customer suppoer at contact@metricsnavigator.ai.",
          sender: "bot",
        };
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
      }
    }
  };

  const handleSuggestionClick = async (
    questionId: number,
    question: string
  ) => {
    try {
      const response = await getAnswer(questionId);
      const userClickedSuggestion: Message = {
        text: question,
        sender: "user",
      };
      setMessages((prevMessages) => [...prevMessages, userClickedSuggestion]);

      const data = response.data;
      if (data && data.answer) {
        const botResponse: Message = { text: data.answer, sender: "bot" };
        setMessages((prevMessages) => [...prevMessages, botResponse]);
      } else {
        const botResponse: Message = {
          text: data.message,
          sender: "bot",
        };
        setMessages((prevMessages) => [...prevMessages, botResponse]);
      }
    } catch (error) {
      console.error("Error fetching answer:", error);
      const errorMessage: Message = {
        text: "Sorry, something went wrong while fetching the answer.",
        sender: "bot",
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInput(event.target.value);
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      id="chatbotContainer"
      className="bg-white rounded-lg shadow-xl max-h-[70svh] w-[450px] flex flex-col"
    >
      <div className="flex justify-between items-center p-4 border-b">
        <h2 className="text-lg font-semibold">Metrics Bot</h2>
        <button className="text-gray-500 hover:text-gray-700" onClick={onClose}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
      <div className="flex-grow p-4 overflow-y-auto">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`mb-2 ${
              message.sender === "user" ? "text-right" : "text-left"
            }`}
          >
            {message.isSuggestion ? (
              <div className="bg-gray-200 text-gray-800 p-2 rounded-lg inline-block max-w-[400px] overflow-hidden text-ellipsis">
                <p className="font-semibold">{message.text}</p>
                <ul className="mt-2 space-y-1">
                  {message.suggestions?.map((suggestion) => (
                    <li
                      key={suggestion.id}
                      className="cursor-pointer text-blue-600 hover:underline"
                      onClick={() =>
                        handleSuggestionClick(
                          suggestion.id,
                          suggestion.question
                        )
                      }
                    >
                      {suggestion.question}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <span
                className={`inline-block p-2 rounded-lg min-w-content max-w-[400px] overflow-hidden text-ellipsis text-align-right ${
                  message.sender === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-800"
                }`}
              >
                {message.text}
              </span>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-4 border-t flex">
        <input
          type="text"
          className="flex-grow p-2 border rounded-l-md focus:outline-none"
          placeholder="Type your message..."
          value={input}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
        />
        <button
          className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-r-md focus:outline-none"
          onClick={handleSend}
        >
          <SendHorizontal />
        </button>
      </div>
    </div>
  );
};

export default ChatModal;
