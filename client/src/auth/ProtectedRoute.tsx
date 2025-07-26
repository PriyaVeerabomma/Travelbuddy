import { useAuth0 } from "@auth0/auth0-react";
import { Navigate, Outlet } from "react-router-dom";
import { toast } from "sonner"

const ProtectedRoute = () => { 
    const { isAuthenticated,isLoading } = useAuth0();

    if(isLoading) return null;
    
    if(isAuthenticated) return <Outlet />;
    // Show toast notification before redirecting
    toast.error("Please log in to access this page", {
        position: "top-right",
        duration: 3000
    });
    return <Navigate to="/" replace />;
    }

export default ProtectedRoute;