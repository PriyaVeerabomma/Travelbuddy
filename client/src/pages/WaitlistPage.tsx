// src/pages/WaitlistPage.tsx
import { useState } from "react";
import { Send, Sparkles, Loader2, CheckCircle } from "lucide-react";

// Import shadcn components
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import Layout from "@/layouts/layout";

const WaitlistPage = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    interests: ""
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Email validation function
  const isValidEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    } else if (formData.name.length < 2) {
      newErrors.name = "Name must be at least 2 characters";
    }
    
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field when user types
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // Form submission handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Submit to Formspree
      const response = await fetch("https://formspree.io/f/meoabraq", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Submission failed");
      }
      
      // Show success state
      setIsSuccess(true);
      setFormData({
        name: "",
        email: "",
        interests: ""
      });
      
      // Reset success state after 3 seconds
      setTimeout(() => {
        setIsSuccess(false);
      }, 3000);
      
    } catch (err) {
      console.error("Submission error:", err);
      setErrors({ form: "Failed to submit. Please try again later." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout showSidebar={false} showHero={false} showFooter={false}>
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] px-4 md:px-6 py-8">
        <div className="w-full max-w-md mx-auto">
          <Card className="border shadow-md">
            <CardHeader className="space-y-2 text-center">
              <div className="flex justify-center mb-2">
                <div className="w-12 h-12 rounded-full bg-raspberry/10 flex items-center justify-center">
                  <Sparkles className="h-6 w-6 text-raspberry" />
                </div>
              </div>
              <CardTitle className="text-2xl font-bold">Join Our Waitlist</CardTitle>
              <CardDescription className="text-muted-foreground">
                Be the first to explore our exciting new features when they launch.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-medium">
                    Full Name
                  </label>
                  <Input 
                    id="name"
                    name="name"
                    placeholder="John Doe" 
                    value={formData.name}
                    onChange={handleChange}
                    className={errors.name ? 'border-red-500 focus-visible:ring-red-500' : ''}
                    disabled={isLoading || isSuccess}
                  />
                  {errors.name && (
                    <p className="text-red-500 text-xs">{errors.name}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium">
                    Email
                  </label>
                  <Input 
                    id="email"
                    name="email"
                    type="email"
                    placeholder="john.doe@example.com" 
                    value={formData.email}
                    onChange={handleChange}
                    className={errors.email ? 'border-red-500 focus-visible:ring-red-500' : ''}
                    disabled={isLoading || isSuccess}
                  />
                  {errors.email && (
                    <p className="text-red-500 text-xs">{errors.email}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="interests" className="text-sm font-medium">
                    What features are you most interested in?
                  </label>
                  <Input 
                    id="interests"
                    name="interests"
                    placeholder="AI travel planning, flight search, etc." 
                    value={formData.interests}
                    onChange={handleChange}
                    disabled={isLoading || isSuccess}
                  />
                  <p className="text-xs text-muted-foreground">
                    This helps us prioritize our feature development.
                  </p>
                </div>
                
                {errors.form && (
                  <p className="text-red-500 text-sm">{errors.form}</p>
                )}
                
                {isSuccess && (
                  <p className="text-green-500 text-sm text-center">
                    You've been added to our waitlist! We'll notify you when we launch new features.
                  </p>
                )}
                
                <Button 
                  type="submit" 
                  className="w-full bg-raspberry hover:bg-raspberry/90"
                  disabled={isLoading || isSuccess}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : isSuccess ? (
                    <>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Success
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Join Waitlist
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
            <CardFooter className="flex justify-center border-t pt-4">
              <p className="text-xs text-center text-muted-foreground">
                By joining our waitlist, you agree to receive updates about our services.
                <br />We respect your privacy and will never share your information.
              </p>
            </CardFooter>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default WaitlistPage;