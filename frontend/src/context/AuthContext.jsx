import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginWithGoogle, loginWithDemo, loginWithTelegram, getCurrentUser, logoutUser } from '../api';
import { initTelegramWebApp, getTelegramUser, isTelegramWebApp } from '../utils/telegram';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isTma, setIsTma] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      // 1. Инициализируем Telegram Mini App SDK если открыто в Telegram
      const tg = initTelegramWebApp();
      const inTelegram = isTelegramWebApp();
      setIsTma(inTelegram);

      const storedToken = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('auth_user');
      
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          // ignore
        }
      }

      // 2. Если запущено внутри Telegram — моментальная бесшовная авторизация профиля Telegram
      if (inTelegram && tg) {
        const tgUser = getTelegramUser();
        if (tgUser) {
          try {
            const authRes = await loginWithTelegram(tg.initData, tgUser);
            if (authRes?.user) {
              setUser(authRes.user);
              setLoading(false);
              return;
            }
          } catch (e) {
            console.warn("Telegram auto-login failed:", e);
          }
        }
      }

      // 3. Стандартная сессия для веб-браузеров
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
        isTma,
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
