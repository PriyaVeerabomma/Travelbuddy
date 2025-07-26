import { useMutation } from "@tanstack/react-query";
import { useAuth0 } from "@auth0/auth0-react";

const API_BASE_URL = import.meta.env.VITE_BASE_URL;

// Define types for messages in chat history
type Message = {
  role: string;
  content: string;
};

// Updated request type with chat history, chat_id, and user_email
type TravelQuestion = {
  query: string;
  chat_history?: Message[];
  chat_id?: string;
  user_email?: string;
};

// Response type remains the same
type TravelResponse = {
  status: string;
  answer: string;
  model: string;
};

export const useAskTravelQuestion = () => {
  // Get user information from Auth0
  const { user } = useAuth0();
  
  const askTravelQuestionRequest = async (question: TravelQuestion): Promise<TravelResponse> => {
    // Get email from Auth0 user object if available
    const userEmail = user?.email || question.user_email || "";
    
    // Ensure chat_history is an array of objects with role and content fields
    const validChatHistory = (question.chat_history || []).map(msg => ({
      role: msg.role === "user" || msg.role === "assistant" || msg.role === "system" 
        ? msg.role 
        : "user", // Default to user if invalid role
      content: msg.content || ""
    }));
    
    // Ensure all required fields are included in the request
    const requestData = {
      query: question.query,
      chat_history: validChatHistory,
      chat_id: question.chat_id || "",
      user_email: userEmail
    };

    console.log("Sending request to API:", JSON.stringify(requestData));

    const response = await fetch(`${API_BASE_URL}/api/llm/ask-question`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || "Failed to get answer from Travel AI";
      throw new Error(errorMessage);
    }
    
    return response.json();
  };
  
  const {
    mutateAsync: askQuestion,
    isPending,
    isError,
    isSuccess,
    data: travelResponse,
    reset
  } = useMutation({
    mutationFn: askTravelQuestionRequest
  });
  
  return {
    askQuestion,
    isLoading: isPending,
    isError,
    isSuccess,
    travelResponse,
    reset
  };
};