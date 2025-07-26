// src/components/UseCaseMindmap.tsx
import { useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { PlaneTakeoff, Hotel, Utensils, Compass, MapPin, Calendar, Users, Star, Sparkles, Bot } from 'lucide-react';

export function UseCaseMindmap() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });
  const [activeNode, setActiveNode] = useState<string | null>(null);
  
  const useCases = [
    {
      id: "itinerary",
      icon: <PlaneTakeoff className="h-6 w-6" />,
      title: "Personalized Itineraries",
      description: "Get custom travel plans based on your interests, budget, and travel style",
      color: "bg-raspberry text-white",
      position: { x: 0, y: -220 }
    },
    {
      id: "accommodation",
      icon: <Hotel className="h-6 w-6" />,
      title: "Accommodation Finder",
      description: "Discover perfect places to stay that match your preferences and budget",
      color: "bg-amber text-foreground",
      position: { x: 210, y: -100 }
    },
    {
      id: "food",
      icon: <Utensils className="h-6 w-6" />,
      title: "Dining Recommendations",
      description: "Find local restaurants and cuisine based on your dietary preferences",
      color: "bg-leaf-green text-foreground",
      position: { x: 160, y: 90 }
    },
    {
      id: "activities",
      icon: <Compass className="h-6 w-6" />,
      title: "Activities & Experiences",
      description: "Discover unique experiences and hidden gems at your destination",
      color: "bg-teal-blue text-white",
      position: { x: -10, y: 180 }
    },
    {
      id: "local",
      icon: <MapPin className="h-6 w-6" />,
      title: "Local Insights",
      description: "Get insider tips and cultural information about your destination",
      color: "bg-raspberry/80 text-foreground",
      position: { x: -200, y: 90 }
    },
    {
      id: "planning",
      icon: <Calendar className="h-6 w-6" />,
      title: "Trip Planning",
      description: "Organize your travel schedule with day-by-day planning assistance",
      color: "bg-amber/80 text-foreground",
      position: { x: -210, y: -90 }
    }
  ];

  return (
    <div className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center rounded-full bg-raspberry/10 px-3 py-1 text-sm text-raspberry mb-4"
          >
            <Sparkles className="mr-1 h-3.5 w-3.5" />
            AI Capabilities
          </motion.div>
          
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl md:text-4xl font-medium mb-4"
          >
            What can TravelMood AI do for you?
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-muted-foreground max-w-2xl mx-auto"
          >
            Explore the many ways our AI can enhance your travel experience
          </motion.p>
        </div>
        
        <div ref={ref} className="relative h-[500px] flex items-center justify-center">
          {/* Center node */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={isInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="absolute z-10 w-24 h-24 rounded-full bg-background shadow-xl border-2 border-raspberry flex items-center justify-center"
          >
            <div className="text-center">
              <Bot className="h-8 w-8 text-raspberry mx-auto" />
              <p className="text-sm font-medium mt-1">TravelMood AI</p>
            </div>
          </motion.div>
          
          {/* Connection lines */}
          {useCases.map((useCase) => (
            <motion.div
              key={`line-${useCase.id}`}
              initial={{ opacity: 0 }}
              animate={isInView ? { opacity: activeNode === useCase.id || !activeNode ? 0.5 : 0.2 } : { opacity: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="absolute left-1/2 top-1/2 h-0.5 bg-muted-foreground origin-left"
              style={{
                width: Math.sqrt(Math.pow(useCase.position.x, 2) + Math.pow(useCase.position.y, 2)),
                transform: `rotate(${Math.atan2(useCase.position.y, useCase.position.x) * (180 / Math.PI)}deg)`
              }}
            />
          ))}
          
          {/* Use case nodes */}
          {useCases.map((useCase, index) => (
            <motion.div
              key={useCase.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={isInView ? 
                { 
                  opacity: 1, 
                  scale: activeNode === useCase.id ? 1.1 : 1,
                  x: useCase.position.x,
                  y: useCase.position.y
                } : 
                { opacity: 0, scale: 0.8, x: 0, y: 0 }
              }
              transition={{ 
                duration: 0.5, 
                delay: 0.3 + index * 0.1,
                type: "spring",
                stiffness: 100
              }}
              className={`absolute z-20 w-32 h-32 rounded-full ${useCase.color} shadow-lg flex flex-col items-center justify-center cursor-pointer transition-transform`}
              style={{ left: "calc(50% - 64px)", top: "calc(50% - 64px)" }}
              onMouseEnter={() => setActiveNode(useCase.id)}
              onMouseLeave={() => setActiveNode(null)}
              onClick={() => setActiveNode(activeNode === useCase.id ? null : useCase.id)}
            >
              <div className="text-center p-2">
                {useCase.icon}
                <p className="font-medium text-sm mt-1">{useCase.title}</p>
              </div>
              
              {/* Expanded description */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ 
                  opacity: activeNode === useCase.id ? 1 : 0,
                  scale: activeNode === useCase.id ? 1 : 0.8,
                  pointerEvents: activeNode === useCase.id ? "auto" : "none"
                }}
                transition={{ duration: 0.2 }}
                className="absolute top-full mt-2 bg-background border rounded-lg shadow-lg p-4 w-64 z-30"
              >
                <h4 className="font-medium mb-2">{useCase.title}</h4>
                <p className="text-sm text-muted-foreground">{useCase.description}</p>
              </motion.div>
            </motion.div>
          ))}
        </div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="text-center mt-8 text-sm text-muted-foreground"
        >
          <p>Hover or tap on each capability to learn more</p>
        </motion.div>
      </div>
    </div>
  );
}