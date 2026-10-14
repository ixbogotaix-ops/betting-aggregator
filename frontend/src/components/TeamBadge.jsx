import React, { useState } from 'react';
import { Shield } from 'lucide-react';

// Палитра градиентов для векторных бейджей команд без официальной эмблемы
const BADGE_GRADIENTS = [
  'from-blue-600 via-indigo-600 to-cyan-500 text-cyan-100 border-blue-400/40',
  'from-emerald-600 via-teal-600 to-green-500 text-emerald-100 border-emerald-400/40',
  'from-purple-600 via-violet-600 to-indigo-500 text-purple-100 border-purple-400/40',
  'from-amber-600 via-orange-600 to-yellow-500 text-amber-100 border-amber-400/40',
  'from-rose-600 via-red-600 to-pink-500 text-rose-100 border-rose-400/40',
  'from-sky-600 via-blue-700 to-indigo-800 text-sky-100 border-sky-400/40',
  'from-teal-600 via-cyan-700 to-blue-600 text-teal-100 border-teal-400/40',
  'from-fuchsia-600 via-pink-600 to-rose-600 text-fuchsia-100 border-pink-400/40',
];

// Хэш названия команды для детерминированного подбора цвета
const getGradientIndex = (str = '') => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % BADGE_GRADIENTS.length;
};

// Извлечение аккуратной аббревиатуры (монограммы) из названия клуба/бойца
const getInitials = (name = '') => {
  if (!name) return 'BK';
  
  // Убираем спортивные префиксы
  let clean = name.replace(/^(1\.\s*|1\s+fc\s+|pfc\s+|cf\s+|ca\s+|cd\s+|rc\s+|sc\s+|fsv\s+|fc\s+|fk\s+)/i, '').trim();
  clean = clean.replace(/\b(tc|fc|cf|if|ik|hk|sk|hc|bk|fk|ac|bc)\b/gi, '').trim();
  
  const words = clean.split(/[\s\-_]+/).filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  if (words.length === 1) {
    return words[0].slice(0, 3).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
};

/**
 * Универсальный компонент эмблемы команды:
 * - Если есть валидный CDN-URL логотипа — отображает официальный прозрачный PNG
 * - Если логотип отсутствует или ошибка загрузки — отображает стильный векторный бейдж-щит
 *   с монограммой команды, градиентом и металлической рамкой.
 */
const TeamBadge = ({ teamName = '', logoUrl = '', size = 'md', className = '' }) => {
  const [imageError, setImageError] = useState(false);

  // Валидный ли URL логотипа (исключаем ui-avatars)
  const isValidLogo = Boolean(
    logoUrl && 
    typeof logoUrl === 'string' && 
    logoUrl.startsWith('http') && 
    !logoUrl.includes('ui-avatars.com') && 
    !imageError
  );

  // Размеры контейнера
  const sizeClasses = {
    sm: 'w-9 h-9 min-w-[36px] text-xs rounded-xl p-1',
    md: 'w-12 h-12 min-w-[48px] text-sm rounded-2xl p-1.5',
    lg: 'w-14 h-14 min-w-[56px] text-base rounded-2xl p-2',
  }[size] || 'w-12 h-12 rounded-2xl p-1.5';

  const initials = getInitials(teamName);
  const gradientClass = BADGE_GRADIENTS[getGradientIndex(teamName)];

  return (
    <div 
      className={`relative flex items-center justify-center bg-gray-900/90 ring-1 ring-gray-700/70 shadow-lg shrink-0 overflow-hidden select-none transition-all group-hover:scale-105 group-hover:ring-blue-500/50 ${sizeClasses} ${className}`}
      title={teamName}
    >
      {isValidLogo ? (
        <img
          src={logoUrl}
          alt={teamName}
          loading="lazy"
          className="max-w-full max-h-full object-contain filter drop-shadow-md transition-transform duration-300"
          onError={() => setImageError(true)}
        />
      ) : (
        /* Стилизованный Векторный Бейдж-Щит с монограммой */
        <div className={`w-full h-full flex flex-col items-center justify-center rounded-xl bg-gradient-to-br ${gradientClass} border shadow-inner font-black tracking-wider uppercase leading-none`}>
          <span className="drop-shadow-sm font-extrabold text-white">
            {initials}
          </span>
          <Shield className="w-2.5 h-2.5 opacity-40 mt-0.5" />
        </div>
      )}
    </div>
  );
};

export default TeamBadge;
