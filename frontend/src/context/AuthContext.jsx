import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginWithGoogle, loginWithDemo, getCurrentUser, logoutUser } from '../api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('auth_user');
      
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          // ignore
        }
      }

      if (storedToken) {
        try {
          const freshUser = await getCurrentUser();
          if (freshUser) {
            setUser(freshUser);
          } else {
            setUser(null);
          }
        } catch (e) {
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const handleGoogleLogin = async (credential) => {
    try {
      const res = await loginWithGoogle(credential);
      setUser(res.user);
      return res.user;
    } catch (err) {
      console.error("Ошибка авторизации Google:", err);
      throw err;
    }
  };

  const handleDemoLogin = async () => {
    try {
      const res = await loginWithDemo();
      setUser(res.user);
      return res.user;
    } catch (err) {
      console.error("Ошибка демо-авторизации:", err);
      throw err;
    }
  };

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        loginWithGoogle: handleGoogleLogin,
        loginDemo: handleDemoLogin,
        logout: handleLogout,
        isLoggedIn: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
