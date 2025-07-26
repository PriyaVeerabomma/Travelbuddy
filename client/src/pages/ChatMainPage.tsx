import { LocationProvider, useLocation } from "@/components/LocationContext";
import { TravelMapComponent } from "@/components/TravelMapComponent";
import { useParams } from 'react-router-dom';
import { useChat } from "@/hooks/useChat";
import { PromptSuggestions } from "@/components/ui/prompt-suggestions";
import ChatComponent from "@/components/ChatComponent";
import { useEffect, useCallback } from 'react';
import type { Location } from '@/components/LocationContext';

function ChatArea() {
  const params = useParams();
  const { 
    messages, 
    input, 
    isTyping, 
    isLoading,
    handleInputChange,
    handleSubmit,
    append,
    resetChat
  } = useChat(params.id);
  
  const { addDetectedLocations, clearDetectedLocations } = useLocation();
  const isEmpty = messages.length === 0;

  // Clear locations when starting a new chat
  useEffect(() => {
    if (isEmpty) {
      clearDetectedLocations();
    }
  }, [isEmpty, clearDetectedLocations]);

  // Travel suggestions
  const travelSuggestions = [
    "Plan a vacation to Paris", 
    "Find hotels in New York", 
    "What are good attractions in Tokyo?"
  ];

  // Handler for detected locations - Using useCallback to prevent recreation on every render
  const handleLocationDetected = useCallback((locations: Location[]) => {
    if (locations && locations.length > 0) {
      console.log("Adding locations to map from ChatComponent:", locations);
      addDetectedLocations(locations);
    }
  }, [addDetectedLocations]);

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b bg-white flex justify-between">
        <h2 className="text-xl font-semibold">Travel Assistant</h2>
        {!isEmpty && (
          <button
            onClick={resetChat}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Start New Chat
          </button>
        )}
      </div>
      
      <ChatComponent
        messages={messages}
        input={input}
        isTyping={isTyping}
        isLoading={isLoading}
        isEmpty={isEmpty}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
        onLocationDetected={handleLocationDetected}
      >
        {/* Use PromptSuggestions for empty state */}
        <PromptSuggestions 
          label="Travel Assistant"
          append={append}
          suggestions={travelSuggestions}
        />
      </ChatComponent>
    </div>
  );
}

export default function ChatMainPage() {
  return (
    <LocationProvider>
      <div className="flex flex-col lg:flex-row h-[calc(100vh-64px)] overflow-hidden">
        <div className="w-full lg:w-1/2 h-1/2 lg:h-full border-r">
          <ChatArea />
        </div>
        <div className="w-full lg:w-1/2 h-1/2 lg:h-full">
          <TravelMapComponent />
        </div>
      </div>
    </LocationProvider>
  );
}