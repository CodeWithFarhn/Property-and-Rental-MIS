  import { createContext, useContext, ReactNode, useEffect } from "react";
  import { useGetMe, useLogin, useLogout, User, LoginBody, getGetMeQueryKey } from "@workspace/api-client-react";
  import { useQueryClient } from "@tanstack/react-query";
  import { useLocation } from "wouter";
  
  type AuthContextType = {
    user: User | null;
    isLoading: boolean;
    login: (data: LoginBody) => Promise<void>;
    logout: () => Promise<void>;
    isAuthenticated: boolean;
  };
  
  const AuthContext = createContext<AuthContextType | undefined>(undefined);
  
  export function AuthProvider({ children }: { children: ReactNode }) {
    const queryClient = useQueryClient();
    const [, setLocation] = useLocation();
  
    const { data: user, isLoading, error } = useGetMe({
      query: {
        retry: false,
      }
    });
  
    const loginMutation = useLogin();
    const logoutMutation = useLogout();
  
    const login = async (data: LoginBody) => {
      await loginMutation.mutateAsync({ data });
      await queryClient.invalidateQueries({ queryKey: getGetMeQueryKey() });
      setLocation("/");
    };
  
    const logoutAction = async () => {
      await logoutMutation.mutateAsync();
      queryClient.setQueryData(getGetMeQueryKey(), null);
      setLocation("/login");
    };
  
    return (
      <AuthContext.Provider
        value={{
          user: user || null,
          isLoading,
          login,
          logout: logoutAction,
          isAuthenticated: !!user,
        }}
      >
        {children}
      </AuthContext.Provider>
    );
  }
  
  export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
      throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
  }
  