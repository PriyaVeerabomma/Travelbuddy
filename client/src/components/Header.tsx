import { Link } from "react-router-dom";
import { Menu } from "lucide-react";
import { SidebarTrigger } from "./ui/sidebar";
import MainNav from "./MainNav";
import React, { useEffect } from "react";

type MainHeaderProps = {
    children?: React.ReactNode;
    showSidebar?: boolean; // New prop to control sidebar trigger visibility
};

const Header = ({ children, showSidebar = true }: MainHeaderProps) => {
    // Reference to the sidebar trigger button
    const sidebarTriggerRef = React.useRef<HTMLButtonElement>(null);
    
    // Effect to auto-open the sidebar on component mount
    useEffect(() => {
        // Only trigger the sidebar to open if showSidebar is true
        if (showSidebar && sidebarTriggerRef.current) {
            sidebarTriggerRef.current.click();
        }
    }, [showSidebar]);

    return (
        <header className="h-16 border-b flex items-center px-4 bg-white sticky top-0 z-10">
            <div className="container mx-auto flex justify-between items-center">
                <div className="flex items-center">
                    {/* Only show the sidebar trigger if showSidebar is true */}
                    {showSidebar && (
                        <SidebarTrigger 
                            ref={sidebarTriggerRef}
                            className="flex items-center justify-center w-10 h-10 rounded-md hover:bg-gray-100 mr-4"
                        >
                            <Menu className="h-5 w-5" />
                        </SidebarTrigger>
                    )}
                    <Link to="/" className="font-medium text-xl">TravelBuddy</Link>
                </div>
                
                <div>
                    <MainNav />
                </div>
            </div>
            
            {children}
        </header>
    );
};

export default Header;