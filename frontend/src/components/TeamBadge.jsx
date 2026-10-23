import React, { useState, useEffect } from 'react';
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
  
  // Убираем маркеры резерва, молодежки, дубля, возраста: (рез), (мол), (19), (u19), (2), (b)
  let clean = name.replace(/\((рез|резерв|мол|молодежь|дубль|u?\d+|ii|b|youth)\)/gi, '').trim();
  // Убираем испанские/португальские служебные связки де, дель, ла, да
  clean = clean.replace(/\b(де|дель|ла|да|ди|ван|дер)\b/gi, '').trim();
  // Убираем спортивные префиксы
  clean = clean.replace(/^(1\.\s*|1\s+fc\s+|pfc\s+|cf\s+|ca\s+|cd\s+|rc\s+|sc\s+|fsv\s+|fc\s+|fk\s+)/i, '').trim();
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

const FALLBACK_LOGOS = {
  'бенфика': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',
  'benfica': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',
  'неймеген': 'https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png',
  'нек': 'https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png',
  'нек неймеген': 'https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png',
  'nec nijmegen': 'https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png',
  'лион': 'https://r2.thesportsdb.com/images/media/team/badge/830lrz1757669895.png',
  'асвел': 'https://r2.thesportsdb.com/images/media/team/badge/830lrz1757669895.png',
  'asvel': 'https://r2.thesportsdb.com/images/media/team/badge/830lrz1757669895.png',
  'селтик': 'https://r2.thesportsdb.com/images/media/team/badge/3uv1641758780002.png',
  'celtic': 'https://r2.thesportsdb.com/images/media/team/badge/3uv1641758780002.png',
  'левски': 'https://r2.thesportsdb.com/images/media/team/badge/evevzv1626443555.png',
  'левски софия': 'https://r2.thesportsdb.com/images/media/team/badge/evevzv1626443555.png',
  'реал мадрид': 'https://a.espncdn.com/i/teamlogos/soccer/500/86.png',
  'real madrid': 'https://a.espncdn.com/i/teamlogos/soccer/500/86.png',
};

/**
 * Универсальный компонент эмблемы команды:
 * - Если есть валидный CDN-URL логотипа — отображает официальный прозрачный PNG
 * - Если логотип отсутствует или ошибка загрузки — проверяет fallback-словарь,
 *   а затем отображает стильный векторный бейдж-щит с монограммой.
 */
const TeamBadge = ({ teamName = '', logoUrl = '', size = 'md', className = '' }) => {
  const [imageError, setImageError] = useState(false);
  const [fallbackError, setFallbackError] = useState(false);

  // Сбрасываем ошибку при смене ссылки на логотип или названия команды
  useEffect(() => {
    setImageError(false);
    setFallbackError(false);
  }, [logoUrl, teamName]);

  const cleanKey = (teamName || '').toLowerCase().trim();
  const fallbackUrl = FALLBACK_LOGOS[cleanKey];

  // Валидный ли основной URL логотипа (исключаем ui-avatars)
  const isPrimaryValid = Boolean(
    logoUrl && 
    typeof logoUrl === 'string' && 
    logoUrl.startsWith('http') && 
    !logoUrl.includes('ui-avatars.com') && 
    !imageError
  );

  const effectiveLogoUrl = isPrimaryValid ? logoUrl : (!fallbackError && fallbackUrl ? fallbackUrl : null);
  const isValidLogo = Boolean(effectiveLogoUrl);

  // Размеры контейнера (крупные, заметные и сочные)
  const sizeClasses = {
    xs: 'w-7 h-7 min-w-[28px] text-[10px] rounded-lg p-0.5',
    sm: 'w-10 h-10 min-w-[40px] text-xs rounded-xl p-1',
    md: 'w-13 h-13 min-w-[52px] text-sm rounded-2xl p-1.5',
    lg: 'w-16 h-16 min-w-[64px] text-base rounded-2xl p-2',
    xl: 'w-20 h-20 min-w-[80px] text-lg rounded-3xl p-2.5',
  }[size] || 'w-13 h-13 rounded-2xl p-1.5';

  const initials = getInitials(teamName);
  const gradientClass = BADGE_GRADIENTS[getGradientIndex(teamName)];

  return (
    <div 
      className={`relative flex items-center justify-center bg-gray-950/85 ring-1 ring-gray-700/80 shadow-2xl shrink-0 overflow-hidden select-none transition-all duration-300 group-hover:scale-105 group-hover:ring-blue-500/60 ${sizeClasses} ${className}`}
      title={teamName}
    >
      {isValidLogo ? (
        <img
          src={effectiveLogoUrl}
          alt={teamName}
          loading="lazy"
          className="w-full h-full object-contain filter drop-shadow-[0_3px_6px_rgba(0,0,0,0.6)] transition-transform duration-300 group-hover:scale-105"
          onError={() => {
            if (isPrimaryValid && fallbackUrl && !fallbackError) {
              setImageError(true);
            } else {
              setFallbackError(true);
              setImageError(true);
            }
          }}
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
