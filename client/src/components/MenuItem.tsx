import type { MenuItem } from "../types";
import { Link, useNavigate } from "react-router-dom";
import { MessageSquare, Search, BookmarkIcon, Bell, Lightbulb, Plus, Plane } from "lucide-react";

const MenuItem = () => {
  const navigate = useNavigate();
  
  const handleClick = (e: React.MouseEvent, path: string) => {
    e.preventDefault();
    navigate("/waitlist");
  };

  return (
    <nav className="flex-1 p-4">
      <ul className="space-y-6">
        <li>
          <Link to="/chat" className="flex items-center text-gray-800 hover:text-black" onClick={(e) => handleClick(e, "/chat")}>
            <MessageSquare className="mr-3 h-5 w-5" />
            <span>Chats</span>
          </Link>
        </li>
        <li>
          <Link to="/flights" className="flex items-center text-gray-800 hover:text-black">
            <Plane className="mr-3 h-5 w-5" />
            <span>Flights</span>
          </Link>
        </li>
        <li>
          <Link to="/explore" className="flex items-center text-gray-800 hover:text-black" onClick={(e) => handleClick(e, "/explore")}>
            <Search className="mr-3 h-5 w-5" />
            <span>Explore</span>
          </Link>
        </li>
        <li>
          <Link to="/saved" className="flex items-center text-gray-800 hover:text-black" onClick={(e) => handleClick(e, "/saved")}>
            <BookmarkIcon className="mr-3 h-5 w-5" />
            <span>Saved</span>
          </Link>
        </li>
        <li>
          <Link to="/updates" className="flex items-center text-gray-800 hover:text-black" onClick={(e) => handleClick(e, "/updates")}>
            <Bell className="mr-3 h-5 w-5" />
            <span>Updates</span>
          </Link>
        </li>
        <li>
          <Link to="/inspiration" className="flex items-center text-gray-800 hover:text-black" onClick={(e) => handleClick(e, "/inspiration")}>
            <Lightbulb className="mr-3 h-5 w-5" />
            <span>Inspiration</span>
          </Link>
        </li>
        <li>
          <Link to="/create" className="flex items-center text-gray-800 hover:text-black" onClick={(e) => handleClick(e, "/create")}>
            <Plus className="mr-3 h-5 w-5" />
            <span>Create</span>
          </Link>
        </li>
      </ul>
    </nav>
  );
};

export default MenuItem;