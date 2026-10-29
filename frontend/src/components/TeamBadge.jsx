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
  // Топ-3 Ставки Дня (сегодняшние клубы)
  'аль-шулла': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png',
  'аль шула': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png',
  'al-shoulla': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png',
  'al shoulla': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png',
  'shoulla': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png',

  'аль-вашм': 'https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png',
  'аль вашм': 'https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png',
  'al-washm': 'https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png',
  'al washm': 'https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png',
  'washm': 'https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png',

  'хантерс': 'https://upload.wikimedia.org/wikipedia/en/e/e2/Hunters_FC_logo.png',
  'hunters': 'https://upload.wikimedia.org/wikipedia/en/e/e2/Hunters_FC_logo.png',
  'hunters fc': 'https://upload.wikimedia.org/wikipedia/en/e/e2/Hunters_FC_logo.png',

  'сентрал сталлионс': 'https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png',
  'central stallions': 'https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png',
  'stallions': 'https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png',
  'тюв буганууд': 'https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png',
  'tuv buganuud': 'https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png',

  'каса пиа': 'https://a.espncdn.com/i/teamlogos/soccer/500/21581.png',
  'casa pia': 'https://a.espncdn.com/i/teamlogos/soccer/500/21581.png',
  'casa pia ac': 'https://a.espncdn.com/i/teamlogos/soccer/500/21581.png',

  'спортинг': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',
  'спортинг лиссабон': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',
  'sporting cp': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',
  'sporting lisbon': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',

  // Трек-рекорд и архивные матчи
  'рыбакина': 'https://a.espncdn.com/i/headshots/tennis/players/full/3126.png',
  'елена рыбакина': 'https://a.espncdn.com/i/headshots/tennis/players/full/3126.png',
  'elena rybakina': 'https://a.espncdn.com/i/headshots/tennis/players/full/3126.png',
  'путинцева': 'https://a.espncdn.com/i/headshots/tennis/players/full/1802.png',
  'юлия путинцева': 'https://a.espncdn.com/i/headshots/tennis/players/full/1802.png',
  'yulia putintseva': 'https://a.espncdn.com/i/headshots/tennis/players/full/1802.png',
  'сент-луис блюз': 'https://a.espncdn.com/i/teamlogos/nhl/500/stl.png',
  'st louis blues': 'https://a.espncdn.com/i/teamlogos/nhl/500/stl.png',
  'монреаль канадиенс': 'https://a.espncdn.com/i/teamlogos/nhl/500/mtl.png',
  'montreal canadiens': 'https://a.espncdn.com/i/teamlogos/nhl/500/mtl.png',

  // Другие популярные клубы
  'абха': 'https://a.espncdn.com/i/teamlogos/soccer/500/19532.png',
  'abha': 'https://a.espncdn.com/i/teamlogos/soccer/500/19532.png',
  'аделаида юнайтед': 'https://a.espncdn.com/i/teamlogos/soccer/500/3932.png',
  'adelaide united': 'https://a.espncdn.com/i/teamlogos/soccer/500/3932.png',
  'сеара': 'https://a.espncdn.com/i/teamlogos/soccer/500/6078.png',
  'ceara': 'https://a.espncdn.com/i/teamlogos/soccer/500/6078.png',
  'сантос': 'https://a.espncdn.com/i/teamlogos/soccer/500/2674.png',
  'santos': 'https://a.espncdn.com/i/teamlogos/soccer/500/2674.png',
  'атлетико минейро': 'https://a.espncdn.com/i/teamlogos/soccer/500/3445.png',
  'atletico mineiro': 'https://a.espncdn.com/i/teamlogos/soccer/500/3445.png',
  'крузейро': 'https://a.espncdn.com/i/teamlogos/soccer/500/3446.png',
  'cruzeiro': 'https://a.espncdn.com/i/teamlogos/soccer/500/3446.png',
  'бостон брюинз': 'https://a.espncdn.com/i/teamlogos/nhl/500/bos.png',
  'boston bruins': 'https://a.espncdn.com/i/teamlogos/nhl/500/bos.png',
  'кливленд кавальерс': 'https://a.espncdn.com/i/teamlogos/nba/500/cle.png',
  'cleveland cavaliers': 'https://a.espncdn.com/i/teamlogos/nba/500/cle.png',

  // Киберспорт
  'mouz': 'https://img-cdn.hltv.org/teamlogo/k1k_nO29XF1wB4T-sBwD2i.png?ixlib=java-2.1.0&s=1c67e813a3ea5a60e1ad6d7e29bb37fe',
  'liquid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/esports/500/teamliquid.png',
  'team liquid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/esports/500/teamliquid.png',
  'eternal fire': 'https://img-cdn.hltv.org/teamlogo/v1V0vLhGj9Wl1zK_X9R7dY.png?ixlib=java-2.1.0&s=a49e9c8bc460eece7f642457c1ecde0f',
  'spirit': 'https://img-cdn.hltv.org/teamlogo/8jP2lQJj042F7Yx9Qp6N_L.png?ixlib=java-2.1.0&s=e60bf764f5e7c2a71f005e83ec55172f',
  'team spirit': 'https://img-cdn.hltv.org/teamlogo/8jP2lQJj042F7Yx9Qp6N_L.png?ixlib=java-2.1.0&s=e60bf764f5e7c2a71f005e83ec55172f',
  'nemiga': 'https://img-cdn.hltv.org/teamlogo/qCflR529iYm_vH661k1_dZ.png?ixlib=java-2.1.0&s=47b777a8848dcf7d7da8fb15ba5fa095',
  'parivision': 'https://img-cdn.hltv.org/teamlogo/zK16k7G_y08iL_mZ6E74_M.png?ixlib=java-2.1.0&s=f366184d081f26f6eb8b75f8f533925c',

  // Базовые топовые европейские
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
  'барселона': 'https://a.espncdn.com/i/teamlogos/soccer/500/83.png',
  'barcelona': 'https://a.espncdn.com/i/teamlogos/soccer/500/83.png',
  'арсенал': 'https://a.espncdn.com/i/teamlogos/soccer/500/359.png',
  'arsenal': 'https://a.espncdn.com/i/teamlogos/soccer/500/359.png',
  'манчестер сити': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',
  'manchester city': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',
  'ливерпуль': 'https://r2.thesportsdb.com/images/media/team/badge/kfaher1737969724.png',
  'liverpool': 'https://r2.thesportsdb.com/images/media/team/badge/kfaher1737969724.png',
  'челси': 'https://a.espncdn.com/i/teamlogos/soccer/500/363.png',
  'chelsea': 'https://a.espncdn.com/i/teamlogos/soccer/500/363.png',
  'ювентус': 'https://a.espncdn.com/i/teamlogos/soccer/500/111.png',
  'милан': 'https://a.espncdn.com/i/teamlogos/soccer/500/103.png',
  'интер': 'https://a.espncdn.com/i/teamlogos/soccer/500/110.png',
  'бавария': 'https://a.espncdn.com/i/teamlogos/soccer/500/132.png',
  'боруссия д': 'https://a.espncdn.com/i/teamlogos/soccer/500/124.png',
  'псж': 'https://a.espncdn.com/i/teamlogos/soccer/500/160.png',
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
  let fallbackUrl = FALLBACK_LOGOS[cleanKey];
  if (!fallbackUrl) {
    for (const [k, v] of Object.entries(FALLBACK_LOGOS)) {
      if (cleanKey.includes(k) || (k.length > 3 && cleanKey.includes(k))) {
        fallbackUrl = v;
        break;
      }
    }
  }

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

  // Размеры контейнера (гармоничные и строго фиксированные квадраты)
  const sizeClasses = {
    xs: 'w-[28px] h-[28px] min-w-[28px] max-w-[28px] min-h-[28px] max-h-[28px] text-[10px] rounded-lg p-0.5',
    sm: 'w-[36px] h-[36px] min-w-[36px] max-w-[36px] min-h-[36px] max-h-[36px] text-xs rounded-xl p-1',
    md: 'w-[44px] h-[44px] min-w-[44px] max-w-[44px] min-h-[44px] max-h-[44px] text-xs rounded-xl p-1',
    lg: 'w-[56px] h-[56px] min-w-[56px] max-w-[56px] min-h-[56px] max-h-[56px] text-sm rounded-2xl p-1.5',
    xl: 'w-[64px] h-[64px] min-w-[64px] max-w-[64px] min-h-[64px] max-h-[64px] text-base rounded-2xl p-2',
  }[size] || 'w-[44px] h-[44px] min-w-[44px] max-w-[44px] min-h-[44px] max-h-[44px] rounded-xl p-1';

  const initials = getInitials(teamName);
  const gradientClass = BADGE_GRADIENTS[getGradientIndex(teamName)];

  return (
    <div 
      className={`relative aspect-square flex items-center justify-center bg-gray-950/85 ring-1 ring-gray-700/80 shadow-2xl shrink-0 overflow-hidden select-none transition-all duration-300 group-hover:scale-105 group-hover:ring-blue-500/60 ${sizeClasses} ${className}`}
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
