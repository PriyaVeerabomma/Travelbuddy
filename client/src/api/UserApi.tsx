import { User } from "@/types";
import { useAuth0 } from "@auth0/auth0-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

const API_BASE_URL = import.meta.env.VITE_BASE_URL;

type CreateUser = {
    auth0id: string;
    email: string;
};

export const userGetMyUser = () => {
    const { getAccessTokenSilently } = useAuth0();

    const getMyUserRequest = async (): Promise<User> => {
        const accessToken = await getAccessTokenSilently();
        const response = await fetch(`${API_BASE_URL}/api/users`, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${accessToken}`,
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            throw new Error("Failed to fetch user");
        }

        return response.json();
    };

    const { data: currentUser, isPending, isError } = useQuery({
        queryKey: ["fetchCurrentUser"],
        queryFn: getMyUserRequest
    });

    if (isError) {
        toast.error("Failed to fetch user");
    }

    return {
        currentUser,
        isLoading: isPending,
        isError,
    };
};

export const useCreateMyUser = () => {
    const { getAccessTokenSilently } = useAuth0();
  
    const createMyUserRequest = async (user: CreateUser) => {
        const accessToken = await getAccessTokenSilently();
        const response = await fetch(`${API_BASE_URL}/api/users`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${accessToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(user),
        });

        if (!response.ok) {
            throw new Error("Failed to create user");
        }
    };
  
    const {
        mutateAsync: createUser,
        isPending,
        isError,
        isSuccess,
    } = useMutation({
        mutationFn: createMyUserRequest
    });
  
    return {
        createUser,
        isLoading: isPending,
        isError,
        isSuccess,
    };
};

type UpdateUserData = {
    name: string;
    addressLine1: string;
    addressLine2: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
    phone: string;
};

export const useUpdateMyUser = () => {
    const { getAccessTokenSilently } = useAuth0();
    
    const updateUserDataRequest = async (form: UpdateUserData) => {
        const accessToken = await getAccessTokenSilently();
        const response = await fetch(`${API_BASE_URL}/api/users`, {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${accessToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(form),
        });

        if (!response.ok) {
            throw new Error("Failed to update user");
        }
    };
    
    const {
        mutateAsync: updateUser,
        isPending,
        isError,
        isSuccess,
        reset
    } = useMutation({
        mutationFn: updateUserDataRequest
    });

    if (isSuccess) {
        toast.success("User updated successfully");
    }
    
    if (isError) {
        toast.error("Failed to update user");
        reset();
    }
          
    return {
        updateUser,
        isLoading: isPending,
    };
};