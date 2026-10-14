import React, { useState, useEffect } from 'react';
import { Trophy, Activity, Target, Clock, LogIn, Radio } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthModal from './AuthModal';
import UserMenu from './UserMenu';

const MoscowClock = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Format to Moscow Time
  const optionsTime = { timeZone: 'Europe/Moscow', hour: '2-digit', minute: '2-digit', second: '2-digit' };
  const optionsDate = { timeZone: 'Europe/Moscow', day: 'numeric', month: 'long', year: 'numeric' };
  
  const timeString = time.toLocaleTimeString('ru-RU', optionsTime);
  const dateString = time.toLocaleDateString('ru-RU', optionsDate);

  return (
    <div className="hidden lg:flex flex-col items-end justify-center bg-gray-800/40 border border-gray-700/50 rounded-xl px-4 py-1.5 shadow-inner">
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-accent" />
        <span className="text-xl font-black text-white tracking-wider font-mono">{timeString}</span>
      </div>
      <span className="text-xs font-medium text-gray-400 uppercase tracking-widest">Москва • {dateString}</span>
    </div>
  );
};

const Header = ({ onOpenSources }) => {
  const { isLoggedIn } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  return (
    <header className="bg-dark/95 backdrop-blur-md border-b border-gray-800/80 sticky top-0 z-50">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="p-2.5 bg-gradient-to-br from-blue-500/20 via-indigo-500/20 to-purple-500/20 border border-blue-500/30 rounded-2xl shadow-lg shadow-blue-500/10">
              <Trophy className="w-7 h-7 text-accent" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 tracking-tight leading-none">
                AI Sports Aggregator
              </h1>
              <p className="text-[11px] font-semibold text-gray-400 mt-1 hidden sm:block">
                Консенсус топ-капперов & Нейроаналитика
              </p>
            </div>
          </div>

          {/* Right Area: Sources Button, Clock & User/Auth */}
          <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
            {/* Кнопка Мониторинга Источников */}
            <button
              onClick={onOpenSources}
              title="Мониторинг источников и парсеров"
              className="flex items-center gap-1.5 px-3 py-2 sm:py-2.5 rounded-xl bg-gray-800/80 hover:bg-gray-700/80 border border-gray-700/70 text-gray-300 hover:text-white text-xs sm:text-sm font-bold transition-all shadow-sm active:scale-95 group"
            >
              <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span className="hidden sm:inline">Источники</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50"></span>
            </button>

            <MoscowClock />

            {isLoggedIn ? (
              <UserMenu />
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs sm:text-sm shadow-md shadow-blue-500/20 transition-all active:scale-95"
              >
                <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                  <path fill="#ffffff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#ffffff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#ffffff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                  <path fill="#ffffff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                </svg>
                <span>Войти</span>
              </button>
            )}
          </div>

          <AuthModal
            isOpen={isAuthModalOpen}
            onClose={() => setIsAuthModalOpen(false)}
          />
        </div>
      </div>
    </header>
  );
};

export default Header;
