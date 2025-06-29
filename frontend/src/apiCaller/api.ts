import axios from "axios";
import { API_BASE_URL } from "../config/apiConfig";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const greetings = (user_name: string) => {
  return api.get(`/chatbot?user_name=${user_name}`).then((response) => {
    return response.data;
  });
};

export const suggestQuestions = (userInput: string) => {
  return api.post("/chatbot/suggest/", {
    user_input: userInput,
    user_name: "Test User",
  });
};

export const getAnswer = (questionId: number) => {
  return api.get(`/chatbot/answer/${questionId}`);
};

export const saveFeedback = (feedbackData: {
  user_name: string;
  question_id: number;
  score: number;
}) => {
  return api.post("/chatbot/feedback/", {
    ...feedbackData,
    user_name: "Test User",
  });
};

// You can add other API calls here as needed
export const getTopQuestions = () => {
  return api.get("/chatbot/top-questions/");
};

export const logQuery = (queryData: {
  user_name: string;
  raw_query: string;
  matched_question_id: number;
}) => {
  return api.post("/chatbot/log-query/", {
    ...queryData,
    user_name: "Test User",
  });
};
