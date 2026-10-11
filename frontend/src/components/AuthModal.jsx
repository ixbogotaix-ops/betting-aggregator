import React, { useEffect, useState } from 'react';
import { X, Shield, Sparkles, CheckCircle, Info, UserCheck, LogIn } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AuthModal({ isOpen, onClose }) {
  const { loginWithGoogle, loginDemo } = useAuth();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showConfigHelp, setShowConfigHelp] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  useEffect(() => {
    if (!isOpen) {
      setError(null);
      return;
    }

    const initGis = () => {
      if (typeof window !== 'undefined' && window.google && googleClientId) {
        try {
          window.google.accounts.id.initialize({
            client_id: googleClientId,
            callback: async (response) => {
              if (response.credential) {
                setLoading(true);
                setError(null);
                try {
                  await loginWithGoogle(response.credential);
                  onClose();
                } catch (err) {
                  setError("Ошибка проверки токена Google. Попробуйте еще раз.");
                } finally {
                  setLoading(false);
                }
              }
            },
            auto_select: false,
          });

          const btnContainer = document.getElementById("google-signin-container");
          if (btnContainer) {
            btnContainer.innerHTML = '';
            window.google.accounts.id.renderButton(btnContainer, {
              theme: "filled_blue",
              size: "large",
              shape: "pill",
              text: "signin_with",
              locale: "ru",
              width: 280,
            });
          }
        } catch (err) {
          console.error("GIS init error:", err);
        }
      }
    };

    if (typeof window !== 'undefined' && !window.google) {
      const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (!existingScript) {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = () => initGis();
        document.head.appendChild(script);
      } else {
        existingScript.addEventListener('load', () => initGis());
      }
    } else {
      initGis();
    }
  }, [isOpen, googleClientId]);

  if (!isOpen) return null;

  const handleDemoSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      await loginDemo();
      onClose();
    } catch (err) {
      setError("Не удалось выполнить демо-вход");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-md bg-gradient-to-br from-card via-gray-900 to-[#121622] rounded-3xl border border-gray-700/80 p-6 sm:p-8 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Декоративное свечение */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-800 transition-colors z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Заголовок */}
        <div className="text-center mb-6 relative z-10">
          <div className="inline-flex items-center justify-center p-3.5 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/30 rounded-2xl mb-3 shadow-lg">
            <svg className="w-8 h-8" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
          </div>
          <h3 className="text-2xl font-black text-white tracking-tight">
            Вход через Google
          </h3>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Синхронизация избранных матчей, персональные экспрессы и настройки уведомлений
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-300 text-center font-medium">
            {error}
          </div>
        )}

        {/* Кнопки входа */}
        <div className="space-y-3 relative z-10">
          {/* Контейнер для официальной кнопки Google */}
          {googleClientId ? (
            <div className="flex justify-center my-3">
              <div id="google-signin-container"></div>
            </div>
          ) : null}

          {/* Кнопка альтернативного/демо входа */}
          <button
            onClick={handleDemoSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 py-3.5 px-5 rounded-2xl font-bold text-sm bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <UserCheck className="w-5 h-5" />
            <span>{loading ? 'Авторизация...' : (googleClientId ? 'Быстрый демо-вход' : 'Войти через Google Аккаунт')}</span>
          </button>

          {/* Преимущества аккаунта */}
          <div className="p-4 bg-gray-950/60 rounded-2xl border border-gray-800/80 space-y-2 mt-4 text-xs text-gray-300">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Сохранение персональных купонов и истории ставок</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Эксклюзивные сигналы супер-консенсуса</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Безопасный вход без паролей в 1 клик</span>
            </div>
          </div>

          {/* Помощь по настройке Client ID */}
          <div className="pt-2 text-center">
            <button
              onClick={() => setShowConfigHelp(!showConfigHelp)}
              className="text-[11px] text-gray-500 hover:text-gray-300 transition-colors inline-flex items-center gap-1"
            >
              <Info className="w-3 h-3" />
              <span>Как настроить свой Google Client ID?</span>
            </button>

            {showConfigHelp && (
              <div className="mt-2.5 p-3 rounded-xl bg-gray-900 border border-gray-800 text-[11px] text-left text-gray-400 space-y-1 animate-fade-in">
                <p className="font-semibold text-gray-200">Инструкция подключения:</p>
                <p>1. Откройте <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer" className="text-blue-400 underline">Google Cloud Console</a>.</p>
                <p>2. Создайте OAuth 2.0 Client ID (тип: Web application).</p>
                <p>3. В «Authorized JavaScript origins» добавьте: <code>http://45.84.222.76</code> и <code>http://localhost:5173</code>.</p>
                <p>4. Вставьте полученный Client ID в файл <code>.env</code> (параметр <code>VITE_GOOGLE_CLIENT_ID</code>).</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
