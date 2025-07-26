import { useState, useEffect, ChangeEvent, useCallback } from 'react';
import { v4 as uuidv4 } from "uuid";
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';

// Import your Travel AI API
import { useAskTravelQuestion } from '@/api/LLMApi';
import type { TravelResponse } from '@/types';

// Import the database
import { chatDb, Conversation } from '@/db/indexedDb';
import { type Message } from '@/components/ui/chat-message';
import { useLocation, Location } from '@/components/LocationContext';

// Type for API messages
type ApiMessage = {
  role: string;
  content: string;
};

export function useChat(conversationId: string = uuidv4()) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationTitle, setConversationTitle] = useState('New Conversation');
  const [lastResponse, setLastResponse] = useState<TravelResponse | null>(null);
  
  const navigate = useNavigate();
  
  // Get user from Auth0
  const { user } = useAuth0();
  
  // Get location context
  const { addDetectedLocations, clearDetectedLocations } = useLocation();
  
  // Use your Travel AI hook
  const { askQuestion, isLoading } = useAskTravelQuestion();
  
  // Load conversation from IndexedDB when component mounts
  useEffect(() => {
    const loadConversation = async () => {
      await chatDb.init();
      
      if (conversationId) {
        const savedConversation = await chatDb.getConversation(conversationId);
        
        if (savedConversation) {
          setMessages(savedConversation.messages);
          setConversationTitle(savedConversation.title);
        } else {
          const newConversation: Conversation = {
            id: conversationId,
            title: 'New Conversation',
            created_at: Date.now(),
            updated_at: Date.now(),
            messages: []
          };
          
          await chatDb.saveConversation(newConversation);
        }
      }
    };
    
    loadConversation();
  }, [conversationId]);
  
  useEffect(() => {
    const saveMessages = async () => {
      if (messages.length > 0 && conversationId) {
        const existingConversation = await chatDb.getConversation(conversationId);
        
        let title = conversationTitle;
        if (messages.length > 0 && messages[0].role === 'user' && title === 'New Conversation') {
          title = messages[0].content.slice(0, 30) + (messages[0].content.length > 30 ? '...' : '');
          setConversationTitle(title);
        }
        
        const conversation: Conversation = {
          id: conversationId,
          title: title,
          created_at: existingConversation?.created_at || Date.now(),
          updated_at: Date.now(),
          messages: messages
        };
        
        await chatDb.saveConversation(conversation);
      }
    };
    
    // Only save if we have messages
    if (messages.length > 0) {
      saveMessages();
    }
  }, [messages, conversationId, conversationTitle]);
  
  // Process the last API response to extract location data
  useEffect(() => {
    if (lastResponse) {
      processResponseForLocations(lastResponse);
    }
  }, [lastResponse]);
  
  // Function to process API response and extract locations
  const processResponseForLocations = useCallback((response: TravelResponse) => {
    try {
      const locations: Location[] = [];
      
      // Process attractions
      if (response.attractions && Array.isArray(response.attractions)) {
        response.attractions.forEach((attraction: any) => {
          if (attraction.location?.lat && attraction.location?.lng) {
            locations.push({
              name: attraction.name,
              lat: attraction.location.lat,
              lng: attraction.location.lng,
              // address: attraction.address,
              // rating: attraction.rating,
              // photo_url: attraction.photo_url,
              // total_ratings: attraction.total_ratings,
              // types: attraction.types,
              type: 'primary' // Set attractions as primary pins
            });
          }
        });
      }
      
      // Process attractions_list structure
      if (response.attractions_list?.attractions && Array.isArray(response.attractions_list.attractions)) {
        response.attractions_list.attractions.forEach((attraction: any) => {
          if (attraction.location?.lat && attraction.location?.lng) {
            locations.push({
              name: attraction.name,
              lat: attraction.location.lat,
              lng: attraction.location.lng,
              // address: attraction.address,
              // rating: attraction.rating,
              // photo_url: attraction.photo_url,
              // total_ratings: attraction.total_ratings,
              // types: attraction.types,
              type: 'primary'
            });
          }
        });
      }
      
      // Process hotels
      if (response.hotels?.data && Array.isArray(response.hotels.data)) {
        response.hotels.data.forEach((hotelOffer: any) => {
          if (hotelOffer.hotel?.location?.lat && hotelOffer.hotel?.location?.lng) {
            locations.push({
              name: hotelOffer.hotel.name,
              lat: hotelOffer.hotel.location.lat,
              lng: hotelOffer.hotel.location.lng,
              // address: hotelOffer.hotel.cityCode || "",
              type: 'secondary', // Set hotels as secondary pins
              relevanceScore: 90
            });
          }
        });
      }
      
      // Process restaurants
      if (response.restaurants && Array.isArray(response.restaurants)) {
        response.restaurants.forEach((restaurant: any) => {
          if (restaurant.location?.lat && restaurant.location?.lng) {
            locations.push({
              name: restaurant.name,
              lat: restaurant.location.lat,
              lng: restaurant.location.lng,
              // address: restaurant.address,
              // rating: restaurant.rating,
              // photo_url: restaurant.photo_url,
              // total_ratings: restaurant.total_ratings,
              // types: restaurant.types,
              type: 'reference' // Set restaurants as reference pins
            });
          }
        });
      }
      
      if (locations.length > 0) {
        console.log("Found locations in API response:", locations);
        addDetectedLocations(locations);
      }
    } catch (err) {
      console.error("Error processing API response for locations:", err);
    }
  }, [addDetectedLocations]);
  
  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };
  
  // Convert our UI messages to API message format
  const formatMessagesForAPI = (msgs: Message[]): ApiMessage[] => {
    // Only include the last 10 messages to avoid making the payload too large
    const recentMessages = msgs.slice(-10);
    
    return recentMessages.map(msg => ({
      // Make sure role is one that OpenAI accepts
      role: msg.role === 'user' || msg.role === 'assistant' ? msg.role : 'user',
      content: msg.content
    }));
  };
  
  const handleSubmit = async (
    event?: { preventDefault?: () => void },
    options?: { experimental_attachments?: FileList }
  ) => {
    event?.preventDefault?.();
    
    if (!input.trim()) return;
    
    // Create user message
    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content: input,
      createdAt: new Date()
    };
    
    // Update UI immediately
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsTyping(true);
    
    try {
      // Format messages for API and send request
      const formattedMessages = formatMessagesForAPI(messages);
      
      console.log("Sending chat history:", formattedMessages);
      
      const response: TravelResponse = await askQuestion({ 
        query: userMessage.content,
        chat_history: formattedMessages,
        chat_id: conversationId,
        user_email: user?.email
      });
      
      // Store the full response for location processing
      setLastResponse(response);
      
      // Create assistant message from response
      const assistantMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: response.answer,
        createdAt: new Date()
      };
      
      // Update messages with assistant response
      setMessages([...updatedMessages, assistantMessage]);
    } catch (error) {
      console.error("Error submitting message:", error);
      // Handle error
      const errorMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: "Sorry, I couldn't process your request. Please try again.",
        createdAt: new Date()
      };
      
      setMessages([...updatedMessages, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };
  
  const append = async (message: {role: string, content: string}) => {
    const newMessage: Message = {
      id: uuidv4(),
      role: message.role as "user" | "assistant",
      content: message.content,
      createdAt: new Date()
    };
    
    const updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);
    
    if (message.role === "user") {
      setIsTyping(true);
      
      // Format messages for API
      const formattedMessages = formatMessagesForAPI(messages);
      
      try {
        const response: TravelResponse = await askQuestion({ 
          query: message.content,
          chat_history: formattedMessages,
          chat_id: conversationId,
          user_email: user?.email
        });
        
        // Store the full response for location processing
        setLastResponse(response);
        
        const assistantMessage: Message = {
          id: uuidv4(),
          role: "assistant",
          content: response.answer,
          createdAt: new Date()
        };
        
        setMessages([...updatedMessages, assistantMessage]);
      } catch (error) {
        console.error("Error appending message:", error);
        const errorMessage: Message = {
          id: uuidv4(),
          role: "assistant",
          content: "Sorry, I couldn't process your request. Please try again.",
          createdAt: new Date()
        };
        
        setMessages([...updatedMessages, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    }
  };
  
  // Function to clear conversation and locations
  const resetChat = useCallback(() => {
    setMessages([]);
    setInput('');
    setLastResponse(null);
    clearDetectedLocations();
  }, [clearDetectedLocations]);
  
  return {
    messages,
    input,
    isTyping,
    isLoading,
    handleInputChange,
    handleSubmit,
    append,
    resetChat
  };
}