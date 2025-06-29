import React from "react";
import { BotMessageSquare, MessageSquareOff } from "lucide-react";

interface FloatingChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

const FloatingChatButton: React.FC<FloatingChatButtonProps> = ({
  isOpen,
  onClick,
}) => {
  return (
    <button
      className="max-w-max max-h-max bg-blue-500 hover:bg-blue-600 text-white p-4 rounded-full shadow-lg focus:outline-none"
      onClick={onClick}
    >
      {!isOpen ? <BotMessageSquare /> : <MessageSquareOff />}
    </button>
  );
};

export default FloatingChatButton;
