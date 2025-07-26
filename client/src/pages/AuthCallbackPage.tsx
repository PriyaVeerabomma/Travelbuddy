import { useCreateMyUser } from "@/api/UserApi";
import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

const AutHCallbackPage = () => {    
    const {user} = useAuth0();
    const {createUser} = useCreateMyUser();
    const naviagte = useNavigate();
    const hasCreatedUser = useRef(false);
    useEffect(() => {
        if(user?.sub && user.email && !hasCreatedUser.current){
            createUser({auth0id:user.sub,email:user.email});
            hasCreatedUser.current = true;
        }
        naviagte("/");
    }, [createUser, naviagte, user]);

    return (
        <>
        Loading....
        </>
    );  
}
export default AutHCallbackPage;