import { ChangeEvent, ReactNode, useRef, useEffect, useState } from 'react';
import { type Message } from '@/components/ui/chat-message';
import { ChatContainer } from '@/components/ui/chat';
import { ChatForm } from '@/components/ui/chat';
import { MessageInput } from '@/components/ui/message-input';
import { ThumbsUp, ThumbsDown, MapPin } from 'lucide-react';
import WeatherDisplay from './WeatherDisplay';
import { useLocation, Location } from './LocationContext';

// Define props including the location detection callback
type ChatComponentProps = {
  messages: Message[];
  input: string;
  isTyping: boolean;
  isLoading: boolean;
  isEmpty: boolean;
  onInputChange: (e: ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (event?: { preventDefault?: () => void }) => void;
  onLocationDetected?: (locations: Location[]) => void;
  children?: ReactNode;
};

export default function ChatComponent({
  messages,
  input,
  isTyping,
  isLoading,
  isEmpty,
  onInputChange,
  onSubmit,
  onLocationDetected,
  children
}: ChatComponentProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const processedMessagesRef = useRef<Set<string>>(new Set());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Process messages for location data
  useEffect(() => {
    if (messages.length > 0 && onLocationDetected) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && !processedMessagesRef.current.has(lastMessage.id)) {
        // Mark this message as processed to prevent reprocessing
        processedMessagesRef.current.add(lastMessage.id);
        processResponseForLocations(lastMessage.content);
      }
    }
  }, [messages, onLocationDetected]);

  // Extract location data from responses
  const processResponseForLocations = (content: string) => {
    if (!content || !onLocationDetected) return;
    
    try {
      // First try to find JSON data in the response
      const jsonMatches = content.match(/({[\s\S]*})/);
      
      if (jsonMatches && jsonMatches[0]) {
        try {
          const jsonStr = jsonMatches[0];
          const data = JSON.parse(jsonStr);
          const locations: Location[] = [];
          
          // Process attractions (from London format)
          if (data.attractions && Array.isArray(data.attractions)) {
            data.attractions.forEach((attraction: any) => {
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
          
          // Process attractions_list (from Boston format)
          if (data.attractions_list?.attractions && Array.isArray(data.attractions_list.attractions)) {
            data.attractions_list.attractions.forEach((attraction: any) => {
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
          if (data.hotels?.data && Array.isArray(data.hotels.data)) {
            data.hotels.data.forEach((hotelOffer: any) => {
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
          if (data.restaurants && Array.isArray(data.restaurants)) {
            data.restaurants.forEach((restaurant: any) => {
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
            console.log("Found locations in JSON:", locations);
            onLocationDetected(locations);
            return;
          }
        } catch (err) {
          console.error("Error parsing JSON:", err);
        }
      }
      
      // Fallback: try to extract coordinates from markdown text
      const locationRegex = /📍.*?(\-?\d+\.\d+),\s*(\-?\d+\.\d+)/g;
      const locations: Location[] = [];
      let match;
      
      while ((match = locationRegex.exec(content)) !== null) {
        const lat = parseFloat(match[1]);
        const lng = parseFloat(match[2]);
        
        if (!isNaN(lat) && !isNaN(lng)) {
          const nameMatch = content.match(/(\w+.*?)\s*📍/);
          const name = nameMatch ? nameMatch[1].trim() : "Location";
          
          locations.push({
            name,
            lat,
            lng,
            type: 'primary'
          });
        }
      }
      
      if (locations.length > 0) {
        console.log("Found locations in text:", locations);
        onLocationDetected(locations);
      }
    } catch (err) {
      console.error("Error processing response for locations:", err);
    }
  };

  const stop = () => {
    // Since your API doesn't support streaming, this is a no-op
    // But we keep it for API compatibility
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] relative">
      <div 
        className="flex-1 overflow-y-auto pr-2 chat-scrollbar"
        ref={chatContainerRef}
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#d1d5db transparent'
        }}
      >
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full">
            {children}
          </div>
        ) : (
          <div className="py-4 px-4">
            {messages.map((message, index) => (
              <div key={message.id} className="mb-4">
                <div className="flex items-start">
                  {/* Avatar */}
                  <div className="mr-3 mt-1">
                    {message.role === "user" ? (
                      <div className="w-8 h-8 rounded-full bg-orange-600 flex items-center justify-center text-white font-semibold">
                        V
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center text-white">
                        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 2L6 7L12 12L18 7L12 2Z" fill="white" />
                          <path d="M12 12L6 7L6 17L12 22L18 17L18 7L12 12Z" fill="white" />
                        </svg>
                      </div>
                    )}
                  </div>

                  {/* Message content */}
                  <div className="flex-1">
                    {/* Message text */}
                    <div className="text-sm prose prose-sm max-w-none">
                      {message.role === "assistant" ? (
                        <>
                          <WeatherDisplay content={message.content} />
                          <div dangerouslySetInnerHTML={{ __html: convertMarkdownToHTML(message.content) }} />
                        </>
                      ) : (
                        <p>{message.content}</p>
                      )}
                    </div>
                    
                    {/* Feedback buttons (only for assistant messages) */}
                    {message.role === "assistant" && (
                      <div className="flex items-center space-x-2 mt-2">
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <ThumbsUp size={16} className="text-gray-500" />
                        </button>
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <ThumbsDown size={16} className="text-gray-500" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {isTyping && (
              <div className="flex items-start">
                <div className="mr-3 mt-1">
                  <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center text-white">
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L6 7L12 12L18 7L12 2Z" fill="white" />
                      <path d="M12 12L6 7L6 17L12 22L18 17L18 7L12 12Z" fill="white" />
                    </svg>
                  </div>
                </div>
                <div className="flex-1">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <div className="px-4 pb-4 sticky bottom-0 bg-white border-t">
        <ChatForm
          className="bg-white rounded-xl border"
          isPending={isLoading || isTyping}
          handleSubmit={onSubmit}
        >
          {({ setFiles }) => (
            <MessageInput
              value={input}
              onChange={onInputChange}
              stop={stop}
              isGenerating={isLoading || isTyping}
              placeholder="Ask anything..."
            />
          )}
        </ChatForm>
      </div>
    </div>
  );
}

// Helper function to convert markdown to HTML
function convertMarkdownToHTML(markdown: string): string {
  // This is a very simple markdown converter
  // In a real app, you might want to use a library like marked.js
  
  // Convert links with location icon
  markdown = markdown.replace(
    /📍 ([^:]+):/g, 
    '<span class="flex items-center"><span class="mr-1"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 13C13.6569 13 15 11.6569 15 10C15 8.34315 13.6569 7 12 7C10.3431 7 9 8.34315 9 10C9 11.6569 10.3431 13 12 13Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 22C16 18 20 14.4183 20 10C20 5.58172 16.4183 2 12 2C7.58172 2 4 5.58172 4 10C4 14.4183 8 18 12 22Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span><strong>$1:</strong></span>'
  );
  
  // Convert numbered lists
  markdown = markdown.replace(
    /^\d+\.\s+(.+)$/gm, 
    '<div class="flex items-start my-2"><span class="mr-2 min-w-[24px] font-bold">$&</span></div>'
  );
  
  // Convert bold text
  markdown = markdown.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  
  // Convert bullet points
  markdown = markdown.replace(
    /^\*\s+(.+)$/gm,
    '<div class="flex items-start my-2"><span class="mr-2">•</span><span>$1</span></div>'
  );
  
  // Convert paragraphs
  markdown = markdown.split('\n\n').map(para => `<p>${para}</p>`).join('');
  
  return markdown;
}