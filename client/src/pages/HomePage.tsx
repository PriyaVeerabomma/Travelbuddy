// src/pages/HomePage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, ChevronRight,Compass, Star, Sparkles,  PlaneTakeoff, Hotel, Utensils, Camera, TrendingUp, Clock} from 'lucide-react';
import { useAuth0 } from "@auth0/auth0-react";
import { useCreateMyUser } from "@/api/UserApi";
// Import shadcn components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { AspectRatio } from "@/components/ui/aspect-ratio";

import { useEffect, useRef } from "react";




import kyotoImg from '../assets/kyoto.jpeg';
import barcelonaImage from '/src/assets/barcelona.jpeg';
import newZealandImage from '/src/assets/new-zealand.jpeg';
import marrakechImage from '/src/assets/marrakech.jpeg';
import testimonial2Image from '/src/assets/testimonial-2.jpeg';
import culturalImage from '/src/assets/cultural.jpeg';
import adventureImage from '/src/assets/adventure.jpeg';
import culinaryImage from '/src/assets/culinary.jpeg';
import luxuryImage from '/src/assets/luxury.jpeg';


// AI-recommended destinations
const aiRecommendedDestinations = [
  {
    name: "Kyoto",
    country: "Japan",
    description: "Traditional temples, serene gardens, and authentic cultural experiences",
    matchScore: 98,
    tags: ["Cultural", "Historical", "Peaceful"],
    imageUrl: kyotoImg
  },
  {
    name: "Barcelona",
    country: "Spain",
    description: "Vibrant architecture, Mediterranean beaches, and lively atmosphere",
    matchScore: 95,
    tags: ["Architecture", "Beach", "Nightlife"],
    imageUrl: barcelonaImage
  },
  {
    name: "New Zealand",
    country: "Oceania",
    description: "Breathtaking landscapes, outdoor adventures, and friendly locals",
    matchScore: 94,
    tags: ["Nature", "Adventure", "Scenic"],
    imageUrl: newZealandImage
  },
  {
    name: "Marrakech",
    country: "Morocco",
    description: "Exotic markets, rich history, and sensory experiences",
    matchScore: 92,
    tags: ["Cultural", "Markets", "Historical"],
    imageUrl: marrakechImage
  },
];

// AI travel insights
const aiTravelInsights = [
  {
    title: "Best time to visit Thailand",
    description: "Our AI analyzed weather patterns, tourist data, and local events to determine November-February offers optimal conditions.",
    category: "Seasonal Insights",
    url: "https://www.enchantingtravels.com/destinations/asia/thailand/best-time-to-visit-thailand/"
  },
  {
    title: "Hidden gems in Portugal",
    description: "Based on local recommendations and off-the-beaten-path locations with high satisfaction ratings.",
    category: "Destination Discovery",
    url:"https://www.europeanbestdestinations.com/destinations/portugal/best-hidden-gems-in-portugal/"
  },
  {
    title: "Budget-friendly European cities",
    description: "Analysis of accommodation, food, and attraction costs across 50+ European destinations.",
    category: "Budget Travel",
    url:"https://travelbinger.com/europe-budget/"
  }
];

// User testimonials
const testimonials = [
  {
    name: "Vishal Prasanna",
    location: "New York",
    comment: "The AI recommended a perfect itinerary for Japan that matched my interests in food and culture perfectly!",
    rating: 5,
    imageUrl: "/assets/testimonials/testimonial-1.jpg"
  },
  {
    name: "Priya Shetty",
    location: "Seattle",
    comment: "Saved me hours of research and created a family-friendly New Zealand trip that everyone loved.",
    rating: 4,
    imageUrl: testimonial2Image
  },
  {
    name: "Srunith",
    location: "London",
    comment: "I was skeptical about AI travel planning, but it found hidden gems in Italy I would have never discovered on my own.",
    rating: 5,
    imageUrl: "/assets/testimonials/testimonial-3.jpg"
  }
];

// Travel categories with images
const travelCategories = [
  {
    name: "Cultural",
    description: "Immersive local experiences",
    icon: <Camera className="h-5 w-5" />,
    color: "raspberry",
    imageUrl: culturalImage
  },
  {
    name: "Adventure",
    description: "Thrilling outdoor activities",
    icon: <Compass className="h-5 w-5" />,
    color: "amber",
    imageUrl: adventureImage
  },
  {
    name: "Culinary",
    description: "Food and drink experiences",
    icon: <Utensils className="h-5 w-5" />,
    color: "leaf-green",
    imageUrl: culinaryImage
  },
  {
    name: "Luxury",
    description: "Premium travel experiences",
    icon: <Hotel className="h-5 w-5" />,
    color: "teal-blue",
    imageUrl: luxuryImage
  }
];

const HomePage = () => {
  // Auth0 user authentication
  //Don't remove this
  const {user} = useAuth0();
  const {createUser} = useCreateMyUser();
  const naviagte = useNavigate();
  const hasCreatedUser = useRef(false);
  useEffect(() => {
      if(user?.sub && user.email && !hasCreatedUser.current){
          createUser({auth0id:user.sub,email:user.email});
          hasCreatedUser.current = true;
      }
      naviagte("/home");
  }, [createUser, naviagte, user]);

  //Don't remove above
  const navigate = useNavigate();
  const [aiPrompt, setAiPrompt] = useState("");

  const handleAiPromptSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (aiPrompt) {
      navigate(`/ai-planner?prompt=${encodeURIComponent(aiPrompt)}`);
    }
  };

  return (
    <div className="flex flex-col gap-16 px-4 md:px-6 py-8 max-w-7xl mx-auto">
      {/* Hero Section with AI Search */}
      <div className="relative">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-raspberry/5 to-transparent rounded-3xl" />
        <div className="py-12 md:py-20 text-center space-y-8">
          
          <div className="space-y-4 max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-medium tracking-tight">
              Your AI travel companion for <span className="text-raspberry">perfect</span> journeys
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Discover personalized travel experiences tailored to your preferences with our advanced AI
            </p>
          </div>

          <Card className="max-w-6xl mx-auto border shadow-md">
            <CardContent className="p-4">
              <Tabs defaultValue="ai" className="w-full">
                <TabsList className="grid grid-cols-1 mb-9">
                  <TabsTrigger value="ai">
                    <Bot className="mr-2 h-4 w-4" />
                    AI Planner
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="ai" className="space-y-4">
                  {/* <div className="text-sm text-muted-foreground mb-2">
                    Describe your perfect trip and our AI will create a personalized plan
                  </div> */}
                  <form onSubmit={handleAiPromptSubmit} className="space-y-4">
                    {/* <div className="relative">
                      <MessageSquare className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                      <textarea 
                        placeholder="I'm looking for a 7-day trip to Japan in April with cultural experiences, good food, and some nature hikes..."
                        className="w-full min-h-[120px] pl-10 pt-2 pr-3 pb-2 rounded-md border border-input bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                        value={aiPrompt}
                        onChange={(e) => setAiPrompt(e.target.value)}
                      />
                    </div> */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      <Badge variant="outline" className="cursor-pointer hover:bg-muted" onClick={() => setAiPrompt("I want a relaxing beach vacation with luxury accommodations")}>
                        Luxury Beach
                      </Badge>
                      <Badge variant="outline" className="cursor-pointer hover:bg-muted" onClick={() => setAiPrompt("Family-friendly European city tour with activities for kids")}>
                        Family Europe
                      </Badge>
                      <Badge variant="outline" className="cursor-pointer hover:bg-muted" onClick={() => setAiPrompt("Adventure trip with hiking and outdoor activities")}>
                        Adventure
                      </Badge>
                      <Badge variant="outline" className="cursor-pointer hover:bg-muted" onClick={() => setAiPrompt("Cultural immersion in Southeast Asia on a budget")}>
                        Cultural Budget
                      </Badge>
                    </div>
                    {/* <Button 
                      className="w-full bg-raspberry hover:bg-raspberry/90"
                      onClick={() => navigate('/waitlist')}
                    >
                      <Sparkles className="mr-2 h-4 w-4" />
                      Join Waitlist to Access AI Planner
                    </Button> */}
                  </form>
                </TabsContent>

                {/* CTA Section */}
                <div className="relative">
                  <div className="absolute inset-0 -z-10 bg-gradient-to-r from-raspberry/10 via-amber/10 to-raspberry/10 rounded-3xl" />
                  <div className="py-12 md:py-16 text-center space-y-8">
                    <div className="space-y-4 max-w-3xl mx-auto">
                      <h2 className="text-3xl md:text-4xl font-medium">Ready to experience AI-powered travel?</h2>
                      <p className="text-xl text-muted-foreground">
                        Join thousands of travelers who have discovered their perfect journeys with TravelMood AI
                      </p>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                      <Button size="lg" className="bg-raspberry hover:bg-raspberry/90" onClick={() => navigate('/waitlist')}>
                        <Sparkles className="mr-2 h-5 w-5" />
                        Let's Start the journey?
                      </Button>
                      <Button className="cursor-pointer" variant="outline" size="lg">
                        Learn How It Works
                      </Button>
                    </div>
                  </div>
                </div>


              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* AI Match Destinations */}
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-3xl font-medium">AI-Matched Destinations</h2>
              <Badge className="bg-amber/10 text-amber border-none">
                <Sparkles className="h-3 w-3 mr-1" />
                For You
              </Badge>
            </div>
            <p className="text-muted-foreground mt-1">Personalized recommendations based on your preferences and travel history</p>
          </div>
          <Button variant="ghost" className="gap-1 text-raspberry">
            View all <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {aiRecommendedDestinations.map((destination) => (
            <Card
              key={destination.name}
              className="overflow-hidden hover:shadow-md transition-all duration-300 cursor-pointer group"
              onClick={() => navigate(`/destination/${destination.name}`)}
            >
              <AspectRatio ratio={3 / 4} className="bg-muted">
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute inset-0 flex items-end p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <Button variant="secondary" size="sm" className="w-full">
                    Explore
                  </Button>
                </div>
                {/* Destination image */}
                {destination.imageUrl ? (
                  <img 
                    src={destination.imageUrl} 
                    alt={`${destination.name}, ${destination.country}`}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-amber/20 to-raspberry/20">
                    <span className="text-muted-foreground font-medium">{destination.name}</span>
                  </div>
                )}
                <div className="absolute top-3 right-3">
                  <Badge className="bg-raspberry text-white">
                    {destination.matchScore}% Match
                  </Badge>
                </div>
              </AspectRatio>
              <CardContent className="p-4">
                <div className="mb-2">
                  <h3 className="font-medium text-lg">{destination.name}</h3>
                  <p className="text-sm text-muted-foreground">{destination.country}</p>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{destination.description}</p>
                <div className="flex flex-wrap gap-1">
                  {destination.tags.map(tag => (
                    <Badge key={tag} variant="outline" className="text-xs bg-muted/50">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* How AI Enhances Your Travel */}
      <div className="relative">
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-leaf-green/5 via-teal-blue/10 to-leaf-green/5 rounded-3xl" />
        <div className="py-12 space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-3xl md:text-4xl font-medium">How AI enhances your travel experience</h2>
            <p className="text-muted-foreground">Our advanced AI analyzes thousands of data points to create the perfect travel experience</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8">
            <Card className="bg-transparent border-none shadow-none">
              <CardContent className="space-y-4 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-raspberry/10 flex items-center justify-center">
                  <PlaneTakeoff className="h-8 w-8 text-raspberry" />
                </div>
                <h3 className="text-xl font-medium">Personalized Itineraries</h3>
                <p className="text-muted-foreground">
                  AI creates custom travel plans based on your interests, pace preferences, and travel style
                </p>
              </CardContent>
            </Card>

            <Card className="bg-transparent border-none shadow-none">
              <CardContent className="space-y-4 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-amber/10 flex items-center justify-center">
                  <Compass className="h-8 w-8 text-amber" />
                </div>
                <h3 className="text-xl font-medium">Hidden Gem Discovery</h3>
                <p className="text-muted-foreground">
                  Uncover lesser-known attractions and experiences that match your unique preferences
                </p>
              </CardContent>
            </Card>

            <Card className="bg-transparent border-none shadow-none">
              <CardContent className="space-y-4 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-leaf-green/10 flex items-center justify-center">
                  <Clock className="h-8 w-8 text-leaf-green" />
                </div>
                <h3 className="text-xl font-medium">Real-time Adaptations</h3>
                <p className="text-muted-foreground">
                  AI adjusts your plans based on weather changes, local events, and real-time availability
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-center mt-8">
            {/* <Button className="bg-raspberry hover:bg-raspberry/90" size="lg">
              <Bot className="mr-2 h-5 w-5" />
              Try AI Planning Now
            </Button> */}
          </div>
        </div>
      </div>

      {/* AI Travel Insights */}
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-medium">AI Travel Insights</h2>
            <p className="text-muted-foreground mt-1">Data-driven travel intelligence to enhance your journey</p>
          </div>
          <Button variant="ghost" className="gap-1 text-raspberry">
            More insights <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {aiTravelInsights.map((insight) => (
            <Card key={insight.title} className="hover:shadow-md transition-all duration-300 cursor-pointer">
              <CardContent className="p-6 space-y-4">
                <Badge className="bg-teal-blue/10 text-teal-blue border-none">
                  {insight.category}
                </Badge>
                <h3 className="text-xl font-medium">{insight.title}</h3>
                <p className="text-muted-foreground">{insight.description}</p>
              </CardContent>


              {/* <CardFooter className="pt-0 pb-6 px-6">
                <Button variant="ghost" className="p-0 h-auto text-raspberry hover:text-raspberry/80">
                  Read full analysis <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </CardFooter> */}

              <CardFooter className="pt-0 pb-6 px-6">
                <Button 
                  variant="ghost" 
                  className="p-0 h-auto text-raspberry hover:text-raspberry/80"
                  onClick={() => window.open(insight.url, '_blank')}
                >
                  Read full analysis <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </CardFooter>


              
            </Card>
          ))}
        </div>
      </div>

      {/* Testimonials */}
      <div className="relative">
        <div className="absolute inset-0 -z-10 bg-muted/30 rounded-3xl" />
        <div className="py-12 space-y-8">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-3xl font-medium mb-4">Travelers love our AI planner</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="bg-background">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center gap-4">
                    {/* Testimonial user avatar */}
                    {testimonial.imageUrl ? (
                      <div className="w-12 h-12 rounded-full overflow-hidden">
                        <img 
                          src={testimonial.imageUrl} 
                          alt={testimonial.name} 
                          className="h-full w-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                        <span className="text-muted-foreground font-medium">{testimonial.name.charAt(0)}</span>
                      </div>
                    )}
                    <div className="flex flex-col">
                      <div className="flex items-center gap-1">
                        {[...Array(5)].map((_, i) => (
                          <Star 
                            key={i} 
                            className={`h-4 w-4 ${i < testimonial.rating ? "fill-amber text-amber" : "text-muted"}`} 
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  <p className="italic">"{testimonial.comment}"</p>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{testimonial.name}</p>
                      <p className="text-sm text-muted-foreground">{testimonial.location}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Travel Categories */}
      <div className="space-y-8">
        <h2 className="text-3xl font-medium">Explore by travel style</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {travelCategories.map((category) => (
            <Card key={category.name} className="cursor-pointer hover:shadow-md transition-all duration-300 group overflow-hidden">
              <AspectRatio ratio={1/1}>
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                <div className="absolute inset-0 flex flex-col justify-end p-4">
                  <div className={`mb-2 bg-${category.color}/80 text-white w-10 h-10 rounded-full flex items-center justify-center`}>
                    {category.icon}
                  </div>
                  <h3 className="text-xl font-medium text-white">{category.name}</h3>
                  <p className="text-white/80 text-sm">{category.description}</p>
                </div>
                {/* Category image */}
                {category.imageUrl ? (
                  <img 
                    src={category.imageUrl} 
                    alt={category.name} 
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className={`h-full w-full bg-gradient-to-br from-${category.color}/20 to-${category.color === 'raspberry' ? 'amber' : category.color === 'amber' ? 'leaf-green' : category.color === 'leaf-green' ? 'teal-blue' : 'raspberry'}/20`} />
                )}
              </AspectRatio>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HomePage;