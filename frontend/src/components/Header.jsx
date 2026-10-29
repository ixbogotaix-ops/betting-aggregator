import React, { useState, useEffect } from 'react';
import { 
  Zap, Trophy, Clock, Radio, Sparkles, Bot, Flame, 
  CalendarDays, CheckCircle2, ChevronRight, Activity, Calculator
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { triggerHaptic } from '../utils/telegram';
import AuthModal from './AuthModal';
import UserMenu from './UserMenu';
import BankrollCalculatorModal from './BankrollCalculatorModal';

const MoscowClock = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const optionsTime = { 
    timeZone: 'Europe/Moscow', 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  };
  const timeString = time.toLocaleTimeString('ru-RU', optionsTime);

  return (
    <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-gray-300 shadow-inner group hover:border-cyan-500/30 transition-colors">
      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></div>
      <span className="text-xs font-mono font-bold tracking-wider text-white">{timeString}</span>
      <span className="text-[10px] text-cyan-400 font-black uppercase tracking-wider">МСК</span>
    </div>
  );
};

const Header = ({ 
  onOpenSources, 
  activeTab = 'botd', 
  setActiveTab = () => {}, 
  botdCount = 0, 
  cappersCount = 0 
}) => {
  const { isLoggedIn } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isCalcOpen, setIsCalcOpen] = useState(false);

  const navTabs = [
    {
      id: 'botd',
      label: 'Ставки Дня',
      icon: Sparkles,
      count: botdCount,
      badgeColor: 'bg-amber-400/20 text-amber-300 border-amber-400/30',
      activeStyle: 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/25 ring-1 ring-amber-400/50',
    },
    {
      id: 'robobet',
      label: 'Робобет ИИ',
      icon: Bot,
      tag: 'AI',
      activeStyle: 'bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 text-white shadow-lg shadow-purple-500/25 ring-1 ring-purple-400/50',
    },
    {
      id: 'cappers',
      label: 'Прогнозы капперов',
      icon: Flame,
      count: cappersCount,
      badgeColor: 'bg-blue-400/20 text-blue-300 border-blue-400/30',
      activeStyle: 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-blue-500/25 ring-1 ring-blue-400/50',
    },
    {
      id: 'parlays',
      label: 'Экспресс Дня',
      icon: Zap,
      activeStyle: 'bg-gradient-to-r from-orange-500 to-red-600 text-white shadow-lg shadow-orange-500/25 ring-1 ring-orange-400/50',
    },
    {
      id: 'matches',
      label: 'Расписание',
      icon: CalendarDays,
      activeStyle: 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/25 ring-1 ring-cyan-400/50',
    },
    {
      id: 'archive',
      label: 'Архив счетов',
      icon: CheckCircle2,
      activeStyle: 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/25 ring-1 ring-emerald-400/50',
    },
    {
      id: 'stats',
      label: 'Рейтинг капперов',
      icon: Trophy,
      activeStyle: 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/25 ring-1 ring-purple-400/50',
    },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#090d16]/95 backdrop-blur-xl border-b border-white/[0.08] shadow-2xl">
      {/* ТИР 1: ВЕРХНЯЯ ШТАТ-ПАНЕЛЬ (Логотип, Часы, Источники, Профиль) */}
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-18 gap-4">
          
          {/* ФУТУРИСТИЧЕСКИЙ КИБЕР-ЛОГОТИП */}
          <div 
            onClick={() => {
              triggerHaptic('light');
              setActiveTab('botd');
            }}
            className="flex items-center gap-3 cursor-pointer group select-none shrink-0"
          >
            <div className="relative flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-[1.5px] shadow-lg shadow-blue-500/25 group-hover:shadow-blue-500/40 group-hover:scale-105 transition-all">
              <div className="w-full h-full bg-[#0a0f1d] rounded-2xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-cyan-400 group-hover:text-white transition-colors" />
              </div>
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-xl sm:text-2xl font-black tracking-tight text-white leading-none">
                  NEURO<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-400">BET</span>
                </span>
                <span className="px-1.5 py-0.5 rounded-md text-[9px] font-black bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 uppercase tracking-widest shadow-sm">
                  AI 2.0
                </span>
              </div>
              <span className="text-[10px] font-semibold text-gray-400 tracking-wide mt-1 hidden sm:block">
                Спортивная нейроаналитика & Консенсус капперов
              </span>
            </div>
          </div>

          {/* ПРАВАЯ ПАНЕЛЬ СТАТУСА: Калькулятор, Парсеры, Часы, Профиль */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* Кнопка Калькулятора Банка / Флэта */}
            <button
              onClick={() => setIsCalcOpen(true)}
              title="Калькулятор банка и размера флэта"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 hover:text-white text-xs font-bold transition-all shadow-sm active:scale-95 group"
            >
              <Calculator className="w-3.5 h-3.5 text-cyan-400 group-hover:rotate-12 transition-transform" />
              <span className="hidden md:inline">Калькулятор</span>
            </button>

            {/* Кнопка Мониторинга Источников */}
            <button
              onClick={onOpenSources}
              title="Мониторинг парсеров и капперов"
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 hover:text-white text-xs font-bold transition-all shadow-sm active:scale-95 group"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
              </span>
              <span className="hidden sm:inline">6 парсеров онлайн</span>
              <span className="sm:hidden">Парсеры</span>
            </button>

            <MoscowClock />

            {isLoggedIn ? (
              <UserMenu />
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-2 px-3.5 py-1.5 sm:py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-black text-xs sm:text-sm shadow-md shadow-blue-500/25 transition-all active:scale-95"
              >
                <span>Войти</span>
              </button>
            )}
          </div>

          <AuthModal
            isOpen={isAuthModalOpen}
            onClose={() => setIsAuthModalOpen(false)}
          />

          <BankrollCalculatorModal 
            isOpen={isCalcOpen}
            onClose={() => setIsCalcOpen(false)}
          />
        </div>
      </div>

      {/* ТИР 2: ВСТРОЕННАЯ НАВИГАЦИЯ ПО РАЗДЕЛАМ (ЕДИНАЯ СТИЛЬНАЯ СТРОКА) */}
      <div className="border-t border-white/[0.06] bg-black/30">
        <div className="max-w-[1440px] mx-auto px-3 sm:px-6 lg:px-8 py-2">
          <nav className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto lg:overflow-visible scrollbar-none py-0.5">
            {navTabs.map((tab) => {
              const isActive = activeTab === tab.id;
              const Icon = tab.icon;

              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    triggerHaptic('light');
                    setActiveTab(tab.id);
                  }}
                  className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer select-none shrink-0 ${
                    isActive
                      ? `${tab.activeStyle} scale-[1.02]`
                      : 'text-gray-400 hover:text-white hover:bg-white/[0.05]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                  <span>{tab.label}</span>

                  {tab.tag && (
                    <span className="px-1.5 py-0.2 rounded-md text-[9px] font-black bg-purple-500/30 text-purple-200 border border-purple-400/40 uppercase">
                      {tab.tag}
                    </span>
                  )}

                  {tab.count !== undefined && tab.count > 0 && (
                    <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-black ${
                      isActive ? 'bg-white/20 text-white' : tab.badgeColor || 'bg-gray-800 text-gray-300'
                    }`}>
                      {tab.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
