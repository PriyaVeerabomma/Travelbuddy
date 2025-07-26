// src/components/StepsSection.tsx
import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Bot, Search, Calendar, MapPin, Sparkles } from 'lucide-react';

export function StepsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });
  
  const steps = [
    {
      icon: <Bot className="h-8 w-8 text-white" />,
      title: "Tell our AI what you want",
      description: "Share your travel preferences, interests, and constraints with our AI assistant",
      color: "bg-raspberry"
    },
    {
      icon: <Search className="h-8 w-8 text-white" />,
      title: "Get personalized recommendations",
      description: "Our AI analyzes thousands of options to find the perfect match for you",
      color: "bg-amber"
    },
    {
      icon: <Calendar className="h-8 w-8 text-white" />,
      title: "Review your custom itinerary",
      description: "Explore day-by-day plans with accommodations, activities, and dining options",
      color: "bg-leaf-green"
    },
    {
      icon: <MapPin className="h-8 w-8 text-white" />,
      title: "Book and enjoy your trip",
      description: "Finalize your plans and enjoy a perfectly tailored travel experience",
      color: "bg-teal-blue"
    }
  ];

  return (
    <div className="py-24 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center rounded-full bg-raspberry/10 px-3 py-1 text-sm text-raspberry mb-4"
          >
            <Sparkles className="mr-1 h-3.5 w-3.5" />
            Simple Process
          </motion.div>
          
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl md:text-4xl font-medium mb-4"
          >
            How TravelMood AI works
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-muted-foreground max-w-2xl mx-auto"
          >
            Our AI-powered platform makes travel planning effortless in just a few simple steps
          </motion.p>
        </div>
        
        <div ref={ref} className="relative">
          {/* Connecting line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-raspberry via-amber to-teal-blue hidden md:block" />
          
          <div className="space-y-16 md:space-y-0">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
                transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                className={`flex flex-col ${index % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'} items-center gap-8 md:gap-16`}
              >
                <div className={`flex-1 ${index % 2 === 0 ? 'md:text-right' : 'md:text-left'}`}>
                  <h3 className="text-2xl font-medium mb-2">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </div>
                
                <div className="relative">
                  <div className={`w-16 h-16 rounded-full ${step.color} flex items-center justify-center shadow-lg z-10 relative`}>
                    {step.icon}
                    <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-raspberry to-amber opacity-20 blur-sm animate-pulse" />
                  </div>
                </div>
                
                <div className="flex-1">
                  {/* Empty div for layout */}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}