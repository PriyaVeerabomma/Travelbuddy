import { useState, useEffect, ChangeEvent } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from "uuid";
import { useAuth0 } from '@auth0/auth0-react';
// Import your Travel AI API
import { useAskTravelQuestion } from '@/api/LLMApi';
import type { TravelResponse } from '@/types';

// Import your custom UI components
import { ChatContainer } from '@/components/ui/chat';
import { ChatForm } from '@/components/ui/chat';
import { MessageList } from '@/components/ui/message-list';
import { MessageInput } from '@/components/ui/message-input';
import { Button } from '@/components/ui/button';
import { type Message } from '@/components/ui/chat-message';

// Import the database
import { chatDb, Conversation } from '@/db/indexedDb';

// Type for API messages
type ApiMessage = {
  role: string;
  content: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationTitle, setConversationTitle] = useState('New Conversation');
  
  const params = useParams();
  const navigate = useNavigate();
  const conversationId = params.id || uuidv4();
  
  // Get user from Auth0
  const { user } = useAuth0();
  
  // Use your Travel AI hook
  const { askQuestion, isLoading } = useAskTravelQuestion();
  
  // Load conversation from IndexedDB when component mounts
  useEffect(() => {
    const loadConversation = async () => {
      await chatDb.init();
      
      if (params.id) {
        const savedConversation = await chatDb.getConversation(params.id);
        
        if (savedConversation) {
          setMessages(savedConversation.messages);
          setConversationTitle(savedConversation.title);
        } else {
          const newConversation: Conversation = {
            id: params.id,
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
  }, [params.id]);
  
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
  
  const append = (message: {role: string, content: string}) => {
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
      
      askQuestion({ 
        query: message.content,
        chat_history: formattedMessages,
        chat_id: conversationId,
        user_email: user?.email
      })
        .then((response: TravelResponse) => {
          const assistantMessage: Message = {
            id: uuidv4(),
            role: "assistant",
            content: response.answer,
            createdAt: new Date()
          };
          
          setMessages([...updatedMessages, assistantMessage]);
          setIsTyping(false);
        })
        .catch((error) => {
          console.error("Error appending message:", error);
          const errorMessage: Message = {
            id: uuidv4(),
            role: "assistant",
            content: "Sorry, I couldn't process your request. Please try again.",
            createdAt: new Date()
          };
          
          setMessages([...updatedMessages, errorMessage]);
          setIsTyping(false);
        });
    }
  };
  
  const stop = () => {
    // Since your API doesn't support streaming, this is a no-op
    // But we keep it for API compatibility
  };
  
  const isEmpty = messages.length === 0;
  
  // For mobile prompt carousel
  const [currentIndex, setCurrentIndex] = useState(0);
  const suggestions = [
    "Plan a vacation to Paris?", 
    "Search a hotel in New York", 
    "Find flights to Tokyo"
  ];
  
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  const handleSuggestionClick = (suggestion: string) => {
    append({
      role: "user",
      content: suggestion,
    });
  };
  
  const nextSuggestion = () => {
    setCurrentIndex((prev) => (prev + 1) % suggestions.length);
  };

  const prevSuggestion = () => {
    setCurrentIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
  };

  // Auto-rotate suggestions every 5 seconds on mobile
  useEffect(() => {
    if (!isMobile || !isEmpty) return;
    
    const interval = setInterval(() => {
      nextSuggestion();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [isMobile, isEmpty, currentIndex]);
  
  return (
    <ChatContainer className="flex flex-col h-[calc(95vh-64px)]">
      <div className="flex-1">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full">
            <h2 className="text-xl font-medium mb-6">Travel Assistant</h2>
            
            {isMobile ? (
              /* Mobile: Show only one suggestion at a time with padding */
              <div className="w-full px-8">
                <div className="relative w-full">
                  <div className="flex items-center">
                    <button 
                      onClick={prevSuggestion}
                      className="p-2 rounded-full hover:bg-gray-100"
                    >
                      <ChevronLeft size={20} />
                    </button>
                    
                    <div className="flex-1 mx-2">
                      <Button
                        variant="outline"
                        className="w-full p-4 h-auto text-base justify-start"
                        onClick={() => handleSuggestionClick(suggestions[currentIndex])}
                      >
                        {suggestions[currentIndex]}
                      </Button>
                    </div>
                    
                    <button 
                      onClick={nextSuggestion}
                      className="p-2 rounded-full hover:bg-gray-100"
                    >
                      <ChevronRight size={20} />
                    </button>
                  </div>
                  
                  {/* Pagination dots */}
                  <div className="flex justify-center mt-4 space-x-2">
                    {suggestions.map((_, index) => (
                      <div 
                        key={index}
                        className={`h-2 w-2 rounded-full cursor-pointer ${
                          index === currentIndex ? 'bg-gray-800' : 'bg-gray-300'
                        }`}
                        onClick={() => setCurrentIndex(index)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* Desktop: Show all suggestions */
              <div className="flex flex-wrap justify-center gap-4 px-4">
                {suggestions.map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    className="p-6 h-auto text-base justify-start"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="chat-messages">
            <MessageList messages={messages} isTyping={isTyping} />
          </div>
        )}
      </div>
      
      <ChatForm
        className="sticky bottom-0 bg-background"
        isPending={isLoading || isTyping}
        handleSubmit={handleSubmit}
      >
        {({ setFiles }) => (
          <MessageInput
            value={input}
            onChange={handleInputChange}
            stop={stop}
            isGenerating={isLoading || isTyping}
          />
        )}
      </ChatForm>
    </ChatContainer>
  );
}

// Media query hook
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => setMatches(event.matches);
    mediaQuery.addEventListener("change", handler);
    
    return () => mediaQuery.removeEventListener("change", handler);
  }, [query]);

  return matches;
}