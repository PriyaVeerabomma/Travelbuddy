


//grok


// import { useChat } from '@ai-sdk/react';
// import { useEffect, useState, useCallback, useRef } from 'react';
// import { ChevronLeft, ChevronRight, MapPin } from 'lucide-react';
// import { LocationProvider, useLocation } from '@/components/LocationContext';
// import { TravelMapComponent } from '@/components/TravelMapComponent';
// import { ChatContainer, ChatForm, MessageList, MessageInput, Button } from '@/components/ui';
// import { type Message } from '@/components/ui/chat-message';
// import { processLocationQuery } from '@/types/geocodingService';



// import { useChat } from '@ai-sdk/react';
// import { useEffect, useState, useCallback, useRef } from 'react';
// import { ChevronLeft, ChevronRight, MapPin } from 'lucide-react';
// import { LocationProvider, useLocation } from '@/components/LocationContext';
// import { TravelMapComponent } from '@/components/TravelMapComponent';
// import { ChatContainer } from '@/components/ui/chat';
// import { ChatForm } from '@/components/ui/chat';
// import { MessageList } from '@/components/ui/message-list';
// import { MessageInput } from '@/components/ui/message-input';
// import { Button } from '@/components/ui/button';
// import { type Message } from '@/components/ui/chat-message';
// import { processLocationQuery } from '@/types/geocodingService';

// function useMediaQuery(query: string): boolean {
//   const [matches, setMatches] = useState(false);

//   useEffect(() => {
//     const mediaQuery = window.matchMedia(query);
//     setMatches(mediaQuery.matches);
//     const handler = (event: MediaQueryListEvent) => setMatches(event.matches);
//     mediaQuery.addEventListener("change", handler);
//     return () => mediaQuery.removeEventListener("change", handler);
//   }, [query]);

//   return matches;
// }

// function ChatArea() {
//   const {
//     messages: aiMessages,
//     input,
//     handleInputChange,
//     handleSubmit: submitChat,
//     append,
//     isLoading,
//     stop,
//   } = useChat();

//   const { addDetectedLocations, clearDetectedLocations, detectedLocations } = useLocation();
//   const [isProcessingLocations, setIsProcessingLocations] = useState(false);
//   const processedMessageIdsRef = useRef<Set<string>>(new Set());

//   const messages: Message[] = aiMessages.map(msg => ({
//     id: msg.id,
//     role: msg.role,
//     content: msg.content?.toString() || "",
//     createdAt: new Date()
//   }));

//   const isEmpty = messages.length === 0;
//   const lastMessage = messages[messages.length - 1] || null;
//   const isTyping = lastMessage?.role === "user";

//   const processLastUserMessage = useCallback(async () => {
//     if (aiMessages.length === 0) return;
//     const last = aiMessages[aiMessages.length - 1];
//     if (last.role !== 'user' || processedMessageIdsRef.current.has(last.id)) return;

//     const content = last.content?.toString().trim();
//     if (!content) return;

//     setIsProcessingLocations(true);
//     try {
//       const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";
//       await processLocationQuery(content, apiKey, (locations) => {
//         if (locations.length > 0) {
//           // Filter out locations with null coordinates
//           const validLocations = locations.filter(loc => loc.lat != null && loc.lng != null);
//           const mockLocations = locations.filter(loc => loc.isMock);
//           if (validLocations.length > 0) {
//             addDetectedLocations(validLocations);
//           }
//           if (mockLocations.length > 0) {
//             console.log("Mock locations detected:", mockLocations);
//             console.log("Geocoding API URL:", `${import.meta.env.VITE_BASE_URL}/api/maps/geocode`);
//             // Optionally notify user about unresolved locations
//           }
//         }
//       });
//       processedMessageIdsRef.current.add(last.id);
//     } catch (err) {
//       console.error("Error processing locations:", err);
//     } finally {
//       setIsProcessingLocations(false);
//     }
//   }, [aiMessages, addDetectedLocations]);

//   useEffect(() => {
//     if (isEmpty) {
//       clearDetectedLocations();
//       processedMessageIdsRef.current.clear();
//     }
//   }, [isEmpty, clearDetectedLocations]);

//   useEffect(() => {
//     if (!isEmpty) processLastUserMessage();
//   }, [aiMessages, processLastUserMessage, isEmpty]);

//   const [currentIndex, setCurrentIndex] = useState(0);
//   const suggestions = [
//     "Plan a vacation to Paris and Rome",
//     "I want to visit Tokyo and explore Kyoto",
//     "Recommend beaches near Miami and hotels in Orlando"
//   ];

//   const isMobile = useMediaQuery('(max-width: 768px)');

//   const handleSuggestionClick = useCallback((text: string) => {
//     append({ role: 'user', content: text });
//   }, [append]);

//   const nextSuggestion = useCallback(() => setCurrentIndex(i => (i + 1) % suggestions.length), [suggestions.length]);
//   const prevSuggestion = useCallback(() => setCurrentIndex(i => (i - 1 + suggestions.length) % suggestions.length), [suggestions.length]);

//   useEffect(() => {
//     if (!isMobile || !isEmpty) return;
//     const interval = setInterval(nextSuggestion, 5000);
//     return () => clearInterval(interval);
//   }, [isMobile, isEmpty, nextSuggestion]);

//   const handleSubmit = useCallback((e: any) => {
//     if (e?.preventDefault) e.preventDefault();
//     submitChat();
//   }, [submitChat]);

//   return (
//     <ChatContainer className="flex flex-col h-[calc(95vh-64px)]">
//       <div className="flex-1">
//         {isEmpty ? (
//           <div className="flex flex-col items-center justify-center h-full">
//             <h2 className="text-xl font-medium mb-6">Try asking about travel destinations</h2>
//             {isMobile ? (
//               <div className="w-full px-8">
//                 <div className="relative w-full">
//                   <div className="flex items-center">
//                     <button onClick={prevSuggestion} className="p-2 rounded-full hover:bg-gray-100">
//                       <ChevronLeft size={20} />
//                     </button>
//                     <div className="flex-1 mx-2">
//                       <Button variant="outline" className="w-full p-4 h-auto text-base justify-start" onClick={() => handleSuggestionClick(suggestions[currentIndex])}>
//                         {suggestions[currentIndex]}
//                       </Button>
//                     </div>
//                     <button onClick={nextSuggestion} className="p-2 rounded-full hover:bg-gray-100">
//                       <ChevronRight size={20} />
//                     </button>
//                   </div>
//                   <div className="flex justify-center mt-4 space-x-2">
//                     {suggestions.map((_, i) => (
//                       <div key={i} className={`h-2 w-2 rounded-full cursor-pointer ${i === currentIndex ? 'bg-gray-800' : 'bg-gray-300'}`} onClick={() => setCurrentIndex(i)} />
//                     ))}
//                   </div>
//                 </div>
//               </div>
//             ) : (
//               <div className="flex flex-wrap justify-center gap-4 px-4">
//                 {suggestions.map(text => (
//                   <Button key={text} variant="outline" className="p-6 h-auto text-base justify-start" onClick={() => handleSuggestionClick(text)}>
//                     {text}
//                   </Button>
//                 ))}
//               </div>
//             )}
//           </div>
//         ) : (
//           <div className="chat-messages">
//             <MessageList messages={messages} isTyping={isTyping || isProcessingLocations} />
//           </div>
//         )}
//       </div>

//       <ChatForm className="sticky bottom-0 bg-background" isPending={isLoading || isTyping || isProcessingLocations} handleSubmit={handleSubmit}>
//         {({ files, setFiles }) => (
//           <MessageInput
//             value={input}
//             onChange={handleInputChange}
//             allowAttachments
//             files={files}
//             setFiles={setFiles}
//             stop={stop}
//             isGenerating={isLoading}
//           />
//         )}
//       </ChatForm>

//       {isProcessingLocations && (
//         <div className="absolute bottom-16 left-4 bg-blue-50 text-blue-700 text-xs py-1 px-2 rounded-md flex items-center">
//           <MapPin className="h-3 w-3 mr-1 animate-pulse" />
//           Processing locations...
//         </div>
//       )}
//     </ChatContainer>
//   );
// }

// export default function ChatPage() {
//   return (
//     <LocationProvider>
//       <div className="flex flex-col lg:flex-row h-[calc(100vh-64px)]">
//         <div className="w-full lg:w-1/2 h-1/2 lg:h-full">
//           <ChatArea />
//         </div>
//         <div className="w-full lg:w-1/2 h-1/2 lg:h-full p-4">
//           <TravelMapComponent />
//         </div>
//       </div>
//     </LocationProvider>
//   );
// }















