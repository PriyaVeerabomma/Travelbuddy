//last try - working 

import { useChat } from '@ai-sdk/react';
import { useEffect, useState, useCallback, useRef } from 'react';
import { MapPin } from 'lucide-react';
import { LocationProvider, useLocation } from '@/components/LocationContext';
import { TravelMapComponent } from '@/components/TravelMapComponent';
import { ChatContainer } from '@/components/ui/chat';
import { ChatForm } from '@/components/ui/chat';
import { MessageList } from '@/components/ui/message-list';
import { MessageInput } from '@/components/ui/message-input';
import { type Message } from '@/components/ui/chat-message';
import { processLocationQuery } from '@/types/geocodingService';

function ChatArea() {
  const {
    messages: aiMessages,
    input,
    handleInputChange,
    handleSubmit: submitChat,
    isLoading,
    stop,
  } = useChat({
    api: '/api/chat',
    onError: (error) => {
      console.error('useChat error:', error);
    }
  });

  const { addDetectedLocations, clearDetectedLocations, detectedLocations } = useLocation();
  const [isProcessingLocations, setIsProcessingLocations] = useState(false);
  const processedContentRef = useRef(new Set<string>());

  const messages: Message[] = aiMessages.map(msg => ({
    id: msg.id,
    role: msg.role,
    content: msg.content?.toString() || "",
    createdAt: new Date()
  }));

  const isEmpty = messages.length === 0;
  const lastMessage = messages[messages.length - 1] || null;
  const isTyping = lastMessage?.role === "user";

  const processLastUserMessage = useCallback(async () => {
    if (aiMessages.length === 0) return;
    const last = aiMessages[aiMessages.length - 1];
    if (last.role !== 'user') return;

    const content = last.content?.toString().trim().toLowerCase();
    if (!content) return;

    // Skip if location already processed
    if (processedContentRef.current.has(content)) {
      console.log('Already processed:', content);
      return;
    }

    // Skip if location already in detectedLocations
    if (detectedLocations.some(loc => loc.name.toLowerCase() === content)) {
      console.log('Location already pinned:', content);
      return;
    }

    console.log('Processing:', content);
    setIsProcessingLocations(true);
    try {
      const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";
      await processLocationQuery(content, apiKey, (locations) => {
        if (locations.length > 0) {
          const validLocations = locations.filter(loc => loc.lat != null && loc.lng != null);
          if (validLocations.length > 0) {
            console.log('Adding locations:', validLocations);
            addDetectedLocations(validLocations);
            processedContentRef.current.add(content);
          }
        }
      });
    } catch (err) {
      console.error("Error processing:", err);
    } finally {
      setIsProcessingLocations(false);
    }
  }, [aiMessages, addDetectedLocations, detectedLocations]);

  useEffect(() => {
    if (isEmpty) {
      clearDetectedLocations();
      processedContentRef.current.clear();
    }
  }, [isEmpty, clearDetectedLocations]);

  useEffect(() => {
    if (!isEmpty && !isProcessingLocations) {
      processLastUserMessage();
    }
  }, [aiMessages, processLastUserMessage, isEmpty, isProcessingLocations]);

  const handleSubmit = useCallback((e: any) => {
    if (e?.preventDefault) e.preventDefault();
    console.log('Submitting:', input);
    submitChat(e);
  }, [submitChat, input]);

  return (
    <ChatContainer className="flex flex-col h-[calc(95vh-64px)]">
      <div className="flex-1">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full">
            <h2 className="text-xl font-medium mb-4">Enter a travel destination</h2>
            <p className="text-gray-500">Type a city, country, or landmark</p>
          </div>
        ) : (
          <div className="chat-messages">
            <MessageList messages={messages} isTyping={isTyping || isProcessingLocations} />
          </div>
        )}
      </div>

      <ChatForm className="sticky bottom-0 bg-background" isPending={isLoading || isTyping || isProcessingLocations} handleSubmit={handleSubmit}>
        {({ files, setFiles }) => (
          <MessageInput
            value={input}
            onChange={handleInputChange}
            allowAttachments
            files={files}
            setFiles={setFiles}
            stop={stop}
            isGenerating={isLoading}
            placeholder="Enter a location (e.g., India)"
          />
        )}
      </ChatForm>

      {isProcessingLocations && (
        <div className="absolute bottom-16 left-4 bg-blue-50 text-blue-700 text-xs py-1 px-2 rounded-md flex items-center">
          <MapPin className="h-3 w-3 mr-1 animate-pulse" />
          Processing...
        </div>
      )}
    </ChatContainer>
  );
}

export default function ChatPage() {
  return (
    <LocationProvider>
      <div className="flex flex-col lg:flex-row h-[calc(100vh-64px)]">
        <div className="w-full lg:w-1/2 h-1/2 lg:h-full">
          <ChatArea />
        </div>
        <div className="w-full lg:w-1/2 h-1/2 lg:h-full p-4">
          <TravelMapComponent />
        </div>
      </div>
    </LocationProvider>
  );
}
