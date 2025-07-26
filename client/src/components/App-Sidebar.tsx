import { Link } from "react-router-dom";
import { MessageSquare, Search, BookmarkIcon, Bell, Lightbulb, Plus, LogIn, Menu } from "lucide-react";
import { useAuth0 } from "@auth0/auth0-react";
import { UsernameMenu } from "./UsernameMenu";
import MenuItem from "./MenuItem";
import {v4 as uuidv4} from "uuid";


export function AppSidebar() {
    const { isAuthenticated, loginWithRedirect, user } = useAuth0();
    
    const generateUniqueId = () => {
        return uuidv4();
    };
    return (
        <div className="flex flex-col h-screen">
            {/* Logo at top */}
            <div className="p-4 border-b">
                <Link to="/home" className="flex items-center">
                    <h1 className="text-xl font-bold">TravelBuddy</h1>
                </Link>
            </div>
            
            {/* Navigation items */}
            <MenuItem />
            
            {/* New chat button */}
            <div className="p-4">
    <Link to={`/chat/${generateUniqueId()}`} className="block">
        <button className="w-full py-2 px-4 bg-gray-100 rounded-full hover:bg-gray-200 text-center">
            New chat
        </button>
    </Link>
</div>
            
            {/* User profile or login button at bottom - fixed position */}
            <div className="mt-auto p-4 border-t">
                {isAuthenticated && user ? (
                    <UsernameMenu user={{
                        name: user.name || user.nickname || 'User',
                        email: user.email || 'No email provided'
                    }}/>
                ) : (
                    <button 
                        onClick={() => loginWithRedirect()}
                        className="w-full py-2 px-4 bg-black text-white rounded-full hover:bg-[#333] flex items-center justify-center"
                    >
                        <LogIn className="mr-2 h-4 w-4" />
                        Log In
                    </button>
                )}
            </div>
            
       
        </div>
    );
}