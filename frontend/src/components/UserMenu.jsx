import React, { useState, useRef, useEffect } from 'react';
import { LogOut, User, Shield, Sparkles, ChevronDown, CheckCircle2, Bookmark } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) return null;

  const initials = (user.name || user.email || 'U')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 p-1.5 pr-3 bg-gray-800/60 hover:bg-gray-800 border border-gray-700/60 hover:border-gray-600 rounded-2xl transition-all shadow-sm group"
      >
        {user.picture ? (
          <img
            src={user.picture}
            alt={user.name || 'User'}
            className="w-8 h-8 rounded-xl object-cover ring-2 ring-blue-500/40"
          />
        ) : (
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-black shadow-inner">
            {initials}
          </div>
        )}

        <div className="hidden sm:flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-white max-w-[110px] truncate group-hover:text-blue-300 transition-colors">
              {user.name || user.email.split('@')[0]}
            </span>
            <span className="text-[10px] uppercase font-black px-1.5 py-0.5 rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">
              {user.role || 'PRO'}
            </span>
          </div>
          <span className="text-[10px] text-gray-400 truncate max-w-[120px]">
            {user.email}
          </span>
        </div>

        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-[#121622] border border-gray-700/80 rounded-2xl shadow-2xl p-2 z-50 animate-fade-in backdrop-blur-xl">
          {/* User Details Header */}
          <div className="p-3 bg-gray-800/40 rounded-xl border border-gray-700/40 mb-2">
            <div className="flex items-center gap-3">
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name || 'User'}
                  className="w-10 h-10 rounded-xl object-cover ring-2 ring-blue-500/40"
                />
              ) : (
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm font-black">
                  {initials}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-white truncate">
                  {user.name || 'Пользователь'}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {user.email}
                </p>
                <div className="flex items-center gap-1 mt-1 text-[11px] text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Google авторизован</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick stats / Features info */}
          <div className="px-3 py-2 text-xs text-gray-400 space-y-1.5 border-b border-gray-800/80 pb-3 mb-2">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-gray-300">
                <Sparkles className="w-3.5 h-3.5 text-yellow-400" /> Тариф
              </span>
              <span className="font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md border border-blue-500/20">
                {user.role === 'admin' ? 'Администратор' : 'PREMIUM PLUS'}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-400">Синхронизация</span>
              <span className="text-emerald-400 font-medium">Активна</span>
            </div>
          </div>

          {/* Logout button */}
          <button
            onClick={() => {
              setIsOpen(false);
              logout();
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Выйти из аккаунта</span>
          </button>
        </div>
      )}
    </div>
  );
}
