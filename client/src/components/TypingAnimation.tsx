import { useState, useEffect } from 'react';

interface TypingAnimationProps {
  texts: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseTime?: number;
}

export const TypingAnimation = ({ 
  texts, 
  typingSpeed = 100, 
  deletingSpeed = 50, 
  pauseTime = 1500 
}: TypingAnimationProps) => {
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  
  useEffect(() => {
    const timeout = setTimeout(() => {
      // Current text to work with
      const fullText = texts[currentTextIndex];
      
      if (!isDeleting) {
        // Typing mode
        setCurrentText(fullText.substring(0, currentText.length + 1));
        
        // If we've typed the full text, start deleting after pause
        if (currentText === fullText) {
          setTimeout(() => {
            setIsDeleting(true);
          }, pauseTime);
        }
      } else {
        // Deleting mode
        setCurrentText(fullText.substring(0, currentText.length - 1));
        
        // If we've deleted everything, move to next text
        if (currentText === '') {
          setIsDeleting(false);
          setCurrentTextIndex((currentTextIndex + 1) % texts.length);
        }
      }
    }, isDeleting ? deletingSpeed : typingSpeed);
    
    return () => clearTimeout(timeout);
  }, [currentText, currentTextIndex, isDeleting, texts, typingSpeed, deletingSpeed, pauseTime]);
  
  return (
    <div className="relative">
      <span className="text-foreground">{currentText}</span>
      <span className="absolute ml-1 inline-block h-5 w-0.5 bg-raspberry animate-blink"></span>
    </div>
  );
};

export default TypingAnimation;