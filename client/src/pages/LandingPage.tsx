// src/pages/LandingPage.tsx
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, useInView, useAnimation } from "framer-motion";
import { ArrowRight, Bot, Globe, Shield, Sparkles, Star, MapPin, Calendar, Users, PlaneTakeoff, Hotel, Utensils, Compass } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
// import { SignInDialog } from "@/components/SignInDialog";
import { StepsSection } from "@/components/StepsSection";
import { UseCaseMindmap } from "@/components/UseCaseMindmap";
import { useAuth0 } from "@auth0/auth0-react";


// Features and testimonials arrays remain the same as in previous code...

const LandingPage = () => {
  const navigate = useNavigate();
  const [isSignInOpen, setIsSignInOpen] = useState(false);
  
  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-b from-raspberry/5 to-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-20 md:py-28 flex flex-col md:flex-row items-center justify-between gap-12">
            {/* Left side content */}
            <div className="flex-1 space-y-8">
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="inline-flex items-center rounded-full bg-raspberry/10 px-3 py-1 text-sm text-raspberry"
              >
                <Sparkles className="mr-1 h-3.5 w-3.5" />
                AI-Powered Travel Planning
              </motion.div>
              
              <motion.h1 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="text-4xl md:text-6xl font-medium tracking-tight"
              >
                Your <span className="text-raspberry">AI travel companion</span> for perfect journeys
              </motion.h1>
              
              <motion.p 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-xl text-muted-foreground max-w-lg"
              >
                Discover personalized travel experiences tailored to your preferences with our advanced AI technology.
              </motion.p>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="flex flex-wrap gap-4"
              >
                <Button 
                  size="lg" 
                  className="bg-raspberry hover:bg-raspberry/90"
                  onClick={() => setIsSignInOpen(true)}
                >
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                
                <Button 
                  variant="outline" 
                  size="lg"
                  onClick={() => window.open("https://github.com/DAMG7245/Travel_Buddy", "_blank")}
                >
                  How It Works
                </Button>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="flex items-center gap-4 text-sm text-muted-foreground"
              >
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div 
                      key={i} 
                      className="w-8 h-8 rounded-full border-2 border-background bg-muted flex items-center justify-center"
                    >
                      {i}
                    </div>
                  ))}
                </div>
                <span>Join 50,000+ travelers using AI to plan their trips</span>
              </motion.div>
            </div>
            
            {/* Right side image/preview */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex-1 w-full max-w-md"
            >
              <div className="relative">
                <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-raspberry to-amber opacity-20 blur-lg"></div>
                <Card className="relative border shadow-xl">
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <Bot className="h-5 w-5 text-raspberry" />
                        <h3 className="font-medium">AI Travel Assistant</h3>
                      </div>
                      
                      <div className="bg-muted/50 p-3 rounded-lg text-sm">
                        I want to plan a 7-day trip to Japan in April with a mix of cultural experiences and nature.
                      </div>
                      
                      <div className="bg-raspberry/10 p-3 rounded-lg text-sm border-l-2 border-raspberry">
                        <p className="font-medium mb-2">Your personalized Japan itinerary:</p>
                        <ul className="list-disc pl-5 space-y-1">
                          <li>Days 1-3: Tokyo (Shibuya, Asakusa Temple, Ueno Park)</li>
                          <li>Days 4-5: Kyoto (Arashiyama Bamboo Grove, Fushimi Inari)</li>
                          <li>Days 6-7: Hakone (Mt. Fuji views, hot springs)</li>
                        </ul>
                      </div>
                      
                      <Button className="w-full bg-raspberry hover:bg-raspberry/90">
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate Complete Itinerary
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
      
      
      {/* Interactive Use Case Mindmap - NEW COMPONENT */}
      <UseCaseMindmap />
      
      {/* Interactive Steps Section - NEW COMPONENT */}
      <StepsSection />
      
    </div>
  );
};

export default LandingPage;