import { useState } from 'react';
import { Search, MapPin, CalendarIcon, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import TypingAnimation from './TypingAnimation';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
 
const Hero = () => {
  const [destination, setDestination] = useState('');
  const [date, setDate] = useState(null);
 
  return (
    <div className="relative overflow-hidden bg-background py-20 md:py-28">
      {/* Abstract background elements */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-raspberry/5 via-background to-amber/5" />
        
        {/* Static circles (for better performance) */}
        <div className="absolute -top-20 -right-20 h-64 w-64 rounded-full bg-raspberry/5 animate-pulse" />
        <div className="absolute top-40 -left-20 h-80 w-80 rounded-full bg-amber/5 animate-pulse" />
        
        {/* Decorative lines */}
        <div className="absolute top-1/4 left-0 right-0 h-px bg-gradient-to-r from-transparent via-raspberry/20 to-transparent" />
        <div className="absolute top-3/4 left-0 right-0 h-px bg-gradient-to-r from-transparent via-amber/20 to-transparent" />
      </div>
 
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-3xl mx-auto text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-medium tracking-tight mb-6">
            Discover the world with <span className="text-raspberry">AI-powered</span> guidance
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Personalized travel experiences tailored to your preferences
          </p>
          <Card className="bg-background/80 backdrop-blur-sm border shadow-lg">
  <CardContent className="p-6">
    <div className="flex items-center gap-3">
      <Search className="h-5 w-5 text-muted-foreground" />
      <TypingAnimation
        texts={[
          "Where would you like to go?",
          "Planning a beach vacation?",
          "Looking for adventure destinations?"
        ]}
      />
    </div>
  </CardContent>
 
          </Card>
        </div>
        
        {/* Featured destinations pills */}
        <div className="flex flex-wrap justify-center gap-2 mt-8">
          <div className="text-sm text-muted-foreground mr-2 flex items-center">
            Popular:
          </div>
          {['Paris', 'Tokyo', 'New York', 'Bali', 'Rome'].map((city) => (
            <Button
              key={city}
              variant="outline"
              size="sm"
              className="rounded-full bg-background/50 backdrop-blur-sm hover:bg-background/80 hover:text-raspberry transition-colors"
            >
              {city}
            </Button>
          ))}
        </div>
        
        {/* Stats or trust indicators */}
        <div className="flex flex-wrap justify-center gap-x-12 gap-y-4 mt-12 text-center text-sm text-muted-foreground">
          <div>
            <p className="font-medium text-foreground text-xl">500k+</p>
            <p>Happy travelers</p>
          </div>
          <div>
            <p className="font-medium text-foreground text-xl">195</p>
            <p>Countries covered</p>
          </div>
          <div>
            <p className="font-medium text-foreground text-xl">4.9/5</p>
            <p>Average rating</p>
          </div>
        </div>
        
        {/* Scroll indicator */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex flex-col items-center animate-bounce -mb-29.5">
          <p className="text-xs text-muted-foreground mb-1">Explore more</p>
          <ArrowRight className="h-4 w-4 rotate-90 text-muted-foreground" />
        </div>
      </div>
    </div>
  );
};
 
export default Hero;