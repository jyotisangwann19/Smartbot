import React, { useState } from "react";
import FloatingChatButton from "./components/FloatingChatButton";
import ChatModal from "./components/ChatModal";
import "./App.css";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const toggleModal = () => {
    setIsModalOpen(!isModalOpen);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to the Chatbot POC</h1>
      </header>

      <div className="fixed max-h-[85svh] min-w-[600px] bottom-[10px] right-[10px] flex flex-col items-end gap-5 p-5">
        <ChatModal isOpen={isModalOpen} onClose={toggleModal} />
        <FloatingChatButton onClick={toggleModal} isOpen={isModalOpen} />
      </div>
    </div>
  );
}

export default App;
