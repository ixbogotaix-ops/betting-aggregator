import React, { useState } from 'react';
import { 
  Target, TrendingUp, Users, Shield, Sparkles, ChevronRight, 
  Clock, MessageSquare, Flame 
} from 'lucide-react';
import MatchDetailModal from './MatchDetailModal';

const formatOutcome = (outcome, homeTeam = '', awayTeam = '') => {
  if (!outcome) return '';
  
  // Очищаем от суффиксов источников в скобках
  let clean = outcome.replace(/\s*\((?:stavka tv|legalbet|vprognoze|br|betting|tg|statarea|pinnacle)\b.*?\)/gi, '').trim().replace(/\.$/, '').trim();
  const low = clean.toLowerCase();
  
  const cleanMatch = (str, target) => {
    if (!str || !target) return false;
    const s = str.toLowerCase().replace(/[^a-zа-я0-9]/g, '');
    const t = target.toLowerCase().replace(/[^a-zа-я0-9]/g, '');
    return s.includes(t) || t.includes(s);
  };

  // 1. Тайм / Матч (КРИТИЧЕСКИ ВАЖНО: отделять от ординаров П1/П2!)
  if (low.includes('тайм / матч') || low.includes('тайм/матч') || low.includes('тайм-матч') || low.includes('т/м:') || /\b(н\/п1|н\/п2|п1\/п1|п2\/п2|п1\/н|п2\/н|п1\/п2|п2\/п1)\b/i.test(low)) {
    const cleanTm = clean.replace(/тайм\s*[\/\-]\s*матч\s*[\-—:]\s*/gi, '').trim();
    return `Тайм/Матч: ${cleanTm}`;
  }

  // 2. Комбинированные ставки
  if (low.includes(' и тб') || low.includes(' и тм') || low.includes(' + тб') || low.includes(' + тм') || low.includes(' и оз') || low.includes(' + оз')) {
    return clean;
  }

  // 3. Обе забьют (ОЗ)
  if (low.includes('оз') || low.includes('обе забьют')) {
    if (low.includes('нет') || low.includes('no') || low.includes('не забьют') || low.includes('— нет') || low.includes('- нет')) {
      return 'Обе забьют — Нет (ОЗ: Нет)';
    }
    return 'Обе забьют — Да (ОЗ: Да)';
  }

  // 4. Двойной шанс
  if (/\b(1x|1х)\b/i.test(low) || (low.includes('не проиграет') && (low.includes('1') || low.includes('хозя') || cleanMatch(low, homeTeam)))) {
    return homeTeam ? `${homeTeam} не проиграет (1X)` : '1X (Хозяева не проиграют)';
  }
  if (/\b(x2|х2)\b/i.test(low) || (low.includes('не проиграет') && (low.includes('2') || low.includes('гост') || cleanMatch(low, awayTeam)))) {
    return awayTeam ? `${awayTeam} не проиграет (X2)` : 'X2 (Гости не проиграют)';
  }
  if (low === '12' || low.includes('победа 1 или 2')) {
    return 'Победа 1 или 2 (12)';
  }

  // 5. Ничья
  if (['draw', 'x', 'х', 'ничья', 'х.', 'x.'].includes(low) || low.startsWith('ничья')) {
    return 'Ничья (Х)';
  }

  // 6. Форы
  const f1 = low.match(/(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?/i);
  if (f1) {
    const v = f1[1].replace(',', '.');
    return homeTeam ? `Фора ${homeTeam} (${v}) (Ф1)` : `Фора 1 (${v})`;
  }
  const f2 = low.match(/(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?/i);
  if (f2) {
    const v = f2[1].replace(',', '.');
    return awayTeam ? `Фора ${awayTeam} (${v}) (Ф2)` : `Фора 2 (${v})`;
  }

  // 7. Тоталы
  const tb = low.match(/(?:тб|больше|over)\s*\(?(\d+[\.,]?\d*)\)?/i);
  if (tb) {
    const v = tb[1].replace(',', '.');
    return `Тотал Больше ${v} (ТБ ${v})`;
  }
  const tm = low.match(/(?:тм|меньше|under)\s*\(?(\d+[\.,]?\d*)\)?/i);
  if (tm) {
    const v = tm[1].replace(',', '.');
    return `Тотал Меньше ${v} (ТМ ${v})`;
  }
  const tot = low.match(/тотал\s*(\d+[\.,]?\d*)/i);
  if (tot) {
    const v = tot[1].replace(',', '.');
    return `Тотал Больше ${v} (ТБ ${v})`;
  }

  // 8. ЧИСТАЯ Победа 2 / Гости (П2)
  if (
    ['away_win', 'п2', 'w2', '2', 'победа 2', 'победа2', 'победа гостей', 'победа второй команды', 'победа второй'].includes(low) ||
    /\b(победа\s*2|победа\s*гостей|победа\s*второй)\b/i.test(low) ||
    /\(п2\)/i.test(low) ||
    /^п2[\.\s]*$/i.test(low) ||
    /^w2[\.\s]*$/i.test(low) ||
    /^2[\.\s]*$/i.test(low)
  ) {
    return awayTeam ? `Победа ${awayTeam} (П2)` : 'Победа Гостей (П2)';
  }

  // 9. ЧИСТАЯ Победа 1 / Хозяева (П1)
  if (
    ['home_win', 'п1', 'w1', '1', 'победа 1', 'победа1', 'победа хозяев', 'победа первой команды', 'победа первой'].includes(low) ||
    /\b(победа\s*1|победа\s*хозяев|победа\s*первой)\b/i.test(low) ||
    /\(п1\)/i.test(low) ||
    /^п1[\.\s]*$/i.test(low) ||
    /^w1[\.\s]*$/i.test(low) ||
    /^1[\.\s]*$/i.test(low)
  ) {
    return homeTeam ? `Победа ${homeTeam} (П1)` : 'Победа Хозяев (П1)';
  }

  // 10. Победа: Название команды
  if (low.startsWith('победа:') || low.startsWith('победа ')) {
    const teamPart = low.includes(':') ? low.split(':')[1].trim() : low.replace('победа', '').trim();
    if (!['тотал', 'тб', 'тм', 'тайм', 'фора'].some(k => teamPart.includes(k))) {
      if (awayTeam && cleanMatch(teamPart, awayTeam)) {
        return `Победа ${awayTeam} (П2)`;
      }
      if (homeTeam && cleanMatch(teamPart, homeTeam)) {
        return `Победа ${homeTeam} (П1)`;
      }
      if (teamPart) {
        return `Победа ${teamPart}`;
      }
    }
  }

  if (awayTeam && cleanMatch(low, awayTeam)) {
    return `Победа ${awayTeam} (П2)`;
  }
  if (homeTeam && cleanMatch(low, homeTeam)) {
    return `Победа ${homeTeam} (П1)`;
  }

  return clean;
};

export const getSportDisplay = (sport, league = '') => {
  const s = `${sport || ''} ${league || ''}`.toLowerCase().trim();
  if (s.includes('mma') || s.includes('ufc') || s.includes('bellator') || s.includes('boxing') || s.includes('martial')) {
    return { name: 'MMA / Бои', icon: '🥊', color: 'from-red-500/20 to-rose-500/10 text-rose-300 border-rose-500/30' };
  }
  if (s.includes('tennis') || s.includes('atp') || s.includes('wta') || s.includes('itf')) {
    return { name: 'Теннис', icon: '🎾', color: 'from-lime-500/20 to-green-500/10 text-lime-300 border-lime-500/30' };
  }
  if (s.includes('basketball') || s.includes('nba') || s.includes('euroleague') || s.includes('vtb') || s.includes('acb')) {
    return { name: 'Баскетбол', icon: '🏀', color: 'from-orange-500/20 to-amber-500/10 text-orange-300 border-orange-500/30' };
  }
  if (!s.includes('veikkausliiga') && (s.includes('hockey') || s.includes('nhl') || s.includes('khl') || s.includes('ahl') || s.includes('shl') || s.includes('liiga') || s.includes('allsvenskan') || s.includes('mestis'))) {
    return { name: 'Хоккей', icon: '🏒', color: 'from-cyan-500/20 to-blue-500/10 text-cyan-300 border-cyan-500/30' };
  }
  if (s.includes('nfl') || s.includes('ncaaf') || s.includes('american football') || s.includes('afl')) {
    return { name: 'Амер. футбол', icon: '🏈', color: 'from-amber-500/20 to-yellow-500/10 text-amber-300 border-amber-500/30' };
  }
  if (s.includes('esport') || s.includes('dota') || s.includes('cs:go') || s.includes('cs2') || s.includes('counter-strike') || s.includes('league of legends') || s.includes('valorant')) {
    return { name: 'Киберспорт', icon: '🎮', color: 'from-purple-500/20 to-pink-500/10 text-purple-300 border-purple-500/30' };
  }
  if (s.includes('baseball') || s.includes('mlb') || s.includes('kbo') || s.includes('npb')) {
    return { name: 'Бейсбол', icon: '⚾', color: 'from-blue-500/20 to-indigo-500/10 text-blue-300 border-blue-500/30' };
  }
  if (s.includes('cricket') || s.includes('twenty20') || s.includes('t20')) {
    return { name: 'Крикет', icon: '🏏', color: 'from-emerald-500/20 to-green-500/10 text-emerald-300 border-emerald-500/30' };
  }
  return { name: 'Футбол', icon: '⚽', color: 'from-blue-500/20 to-indigo-500/10 text-blue-300 border-blue-500/30' };
};

export const getRussianSport = (sport) => getSportDisplay(sport).name.toUpperCase();

const formatCardMoscowTime = (dateStr) => {
  if (!dateStr) return { dateStr: '', timeStr: '' };
  try {
    let cleanStr = String(dateStr).trim().replace(' ', 'T');
    if (!cleanStr.includes('Z') && !cleanStr.includes('+') && !cleanStr.slice(10).includes('-')) {
      cleanStr = `${cleanStr}+03:00`;
    }
    const d = new Date(cleanStr);
    if (isNaN(d.getTime())) {
      const m = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
      if (m) {
        const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
        const day = parseInt(m[3], 10);
        const mIdx = parseInt(m[2], 10) - 1;
        return {
          dateStr: `${day} ${months[mIdx] || ''}`,
          timeStr: `${m[4]}:${m[5]}`
        };
      }
      return { dateStr: '', timeStr: '' };
    }
    const dStr = d.toLocaleDateString('ru-RU', {
      timeZone: 'Europe/Moscow',
      day: 'numeric',
      month: 'short'
    }).replace('.', '');
    const tStr = d.toLocaleTimeString('ru-RU', {
      timeZone: 'Europe/Moscow',
      hour: '2-digit',
      minute: '2-digit'
    });
    return { dateStr: dStr, timeStr: tStr };
  } catch (e) {
    return { dateStr: '', timeStr: '' };
  }
};

const cleanAiInsight = (text) => {
  if (!text) return '';
  let clean = text.replace(/\*\*/g, '').replace(/🔥\s*ИИ-Нейровердикт.*?:/gi, '').trim();
  clean = clean.replace(/^[:\s-]+/, '').trim();
  return clean;
};

const TopBetCard = ({ bet }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  let colorClass = 'bg-accent';
  let textClass = 'text-accent';
  let borderClass = 'border-blue-500/30';
  
  if (bet.confidence_score >= 80) {
    colorClass = 'bg-success';
    textClass = 'text-success';
    borderClass = 'border-emerald-500/30';
  } else if (bet.confidence_score < 60) {
    colorClass = 'bg-warning';
    textClass = 'text-warning';
    borderClass = 'border-amber-500/30';
  }

  // Извлекаем названия команд
  const [homeTeam, awayTeam] = bet.match_name.includes(' vs ') 
    ? bet.match_name.split(' vs ') 
    : bet.match_name.split(' - ');

  const getLogoUrl = (teamName) => 
    `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName || 'Team')}&background=1e293b&color=38bdf8&size=64&bold=true&rounded=true`;

  const sportDisplay = getSportDisplay(bet.sport_type, bet.league);
  const totalCappersCount = bet.all_predictions?.length || bet.supporting_sources?.length || 0;
  const mskTime = formatCardMoscowTime(bet.match_date);

  const sourcesList = (bet.supporting_sources || []).map(s => {
    return s.replace(/\s*\(Рейтинг:.*?\)/g, '').trim();
  });

  const cleanInsight = cleanAiInsight(bet.ai_insight);

  return (
    <>
      <div 
        onClick={() => setIsModalOpen(true)}
        className="h-full flex flex-col justify-between bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 rounded-3xl p-5 border border-gray-800 hover:border-blue-500/50 shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 hover:-translate-y-1.5 cursor-pointer transition-all duration-300 relative overflow-hidden group select-none"
      >
        {/* Фоновое свечение в верхнем углу */}
        <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 rounded-bl-full pointer-events-none blur-xl ${colorClass}`}></div>

        <div>
          {/* ВЕРХНЯЯ ШАПКА: Вид спорта СЛЕВА (Футбол, Хоккей и т.д.), Время СПРАВА */}
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r ${sportDisplay.color} rounded-full text-xs font-black border shadow-sm shrink-0`}>
                <span className="text-sm">{sportDisplay.icon}</span>
                <span className="truncate max-w-[140px] uppercase text-[11px] tracking-wider font-extrabold">
                  {sportDisplay.name}
                </span>
              </span>
            </div>

            {/* Аккуратная плашка времени по Москве */}
            {bet.match_date && (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-950/90 rounded-xl border border-gray-700/80 text-xs font-black text-gray-200 shrink-0 shadow-inner">
                <Clock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="whitespace-nowrap">{mskTime.dateStr}, {mskTime.timeStr}</span>
                <span className="text-[10px] text-blue-400 font-black uppercase tracking-wider">МСК</span>
              </div>
            )}
          </div>

          {/* ПОДШАПКА: Статус "Ставка Дня" + Лига с флагом страны */}
          <div className="flex items-center gap-2 flex-wrap mb-4">
            {bet.is_bet_of_the_day && (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-black text-amber-300 bg-amber-500/15 px-2.5 py-0.5 rounded-lg border border-amber-400/40 shadow-sm animate-pulse">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>СТАВКА ДНЯ</span>
                <span className="text-amber-500/60">•</span>
                <span className="text-amber-200 font-semibold">{sportDisplay.name.toUpperCase()}</span>
              </span>
            )}
            <span className="text-[11px] font-semibold text-gray-400 px-2.5 py-0.5 bg-gray-800/60 rounded-md border border-gray-800 truncate max-w-[190px] inline-flex items-center gap-1.5">
              {bet.country_flag_url && (
                <img 
                  src={bet.country_flag_url} 
                  alt="" 
                  className="w-3.5 h-2.5 object-cover rounded-[2px] opacity-75 shrink-0" 
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              )}
              <span className="truncate">{bet.league || bet.country_name || "Лига"}</span>
            </span>
          </div>

          {/* БЛОК ПРОТИВОСТОЯНИЯ (Эмблемы и Названия с единой сеткой) */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 p-3 bg-gray-950/50 rounded-2xl border border-gray-800/70 mb-4">
            {/* Хозяева */}
            <div className="flex flex-col items-center text-center">
              <div className="w-14 h-14 p-2 bg-gray-850 rounded-2xl flex items-center justify-center mb-1.5 ring-1 ring-gray-700 shadow-md group-hover:ring-blue-500/50 group-hover:scale-105 transition-all">
                <img 
                  src={bet.home_logo || getLogoUrl(homeTeam)} 
                  alt={homeTeam} 
                  className="max-w-full max-h-full object-contain filter drop-shadow-md"
                  onError={(e) => { e.currentTarget.src = getLogoUrl(homeTeam); }}
                />
              </div>
              <span className="text-xs font-bold text-white leading-tight min-h-[2.4rem] flex items-center justify-center line-clamp-2 px-1">
                {homeTeam}
              </span>
              <span className="text-[10px] text-gray-500 font-semibold mt-0.5">Хозяева</span>
            </div>

            {/* Разделитель VS или Счёт матча */}
            <div className="flex flex-col items-center justify-center">
              {bet.final_score_home !== null && bet.final_score_away !== null ? (
                <div className="flex flex-col items-center">
                  <div className="px-2.5 py-1 rounded-xl bg-gray-800/90 border border-gray-600 font-black text-sm text-white shadow-md tracking-wider">
                    {bet.final_score_home} : {bet.final_score_away}
                  </div>
                  <span className="text-[9px] font-black text-emerald-400 uppercase tracking-widest mt-0.5">ФИНАЛ</span>
                </div>
              ) : (
                <span className="w-7 h-7 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-[10px] font-black text-gray-400 italic shadow-inner">
                  VS
                </span>
              )}
            </div>

            {/* Гости */}
            <div className="flex flex-col items-center text-center">
              <div className="w-14 h-14 p-2 bg-gray-850 rounded-2xl flex items-center justify-center mb-1.5 ring-1 ring-gray-700 shadow-md group-hover:ring-purple-500/50 group-hover:scale-105 transition-all">
                <img 
                  src={bet.away_logo || getLogoUrl(awayTeam)} 
                  alt={awayTeam} 
                  className="max-w-full max-h-full object-contain filter drop-shadow-md"
                  onError={(e) => { e.currentTarget.src = getLogoUrl(awayTeam); }}
                />
              </div>
              <span className="text-xs font-bold text-white leading-tight min-h-[2.4rem] flex items-center justify-center line-clamp-2 px-1">
                {awayTeam}
              </span>
              <span className="text-[10px] text-gray-500 font-semibold mt-0.5">Гости</span>
            </div>
          </div>

          {/* КОНСЕНСУС КАППЕРОВ */}
          <div className="mb-4 p-3 bg-gray-950/50 rounded-xl border border-gray-800/80">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-gray-400 font-medium flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-blue-400" />
                <span>Консенсус экспертов</span>
                {totalCappersCount > 0 && (
                  <span className="text-gray-500 text-[11px]">({totalCappersCount})</span>
                )}
              </span>
              <span className={`font-black text-sm ${textClass}`}>{bet.confidence_score}%</span>
            </div>
            <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
              <div 
                className={`h-full ${colorClass} transition-all duration-1000 ease-out`} 
                style={{ width: `${Math.min(bet.confidence_score, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* РЕКОМЕНДУЕМЫЙ ИСХОД И КЭФ (Широкий, удобный, с бейджем результата) */}
          <div className={`p-3.5 bg-gradient-to-br ${
            bet.bet_result === 'win' 
              ? 'from-emerald-950/40 via-gray-900 to-gray-900 border-emerald-500/50' 
              : bet.bet_result === 'loss' 
              ? 'from-rose-950/40 via-gray-900 to-gray-900 border-rose-500/50' 
              : bet.bet_result === 'refund' 
              ? 'from-amber-950/40 via-gray-900 to-gray-900 border-amber-500/50' 
              : 'from-blue-950/40 via-indigo-950/20 to-gray-900 border-blue-500/30'
          } rounded-2xl border mb-3 shadow-inner`}>
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-blue-300 flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-blue-400" />
                <span>Рекомендуемый исход</span>
              </span>
              <div className="flex items-center gap-1.5">
                {bet.bet_result === 'win' && (
                  <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-black rounded-md flex items-center gap-1 animate-pulse">
                    ✅ ЗАШЛА
                  </span>
                )}
                {bet.bet_result === 'loss' && (
                  <span className="px-2 py-0.5 bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-black rounded-md flex items-center gap-1">
                    ❌ МИМО
                  </span>
                )}
                {bet.bet_result === 'refund' && (
                  <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-black rounded-md flex items-center gap-1">
                    🔄 ВОЗВРАТ
                  </span>
                )}
                <span className="px-2.5 py-0.5 bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-black text-sm rounded-lg shadow-sm">
                  КЭФ {bet.average_odds.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="font-black text-white text-base leading-snug">
              {formatOutcome(bet.recommended_outcome, homeTeam, awayTeam)}
            </div>
          </div>

          {/* ИСТОЧНИКИ */}
          {sourcesList.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-950/40 px-3 py-2 rounded-xl mb-3 border border-gray-800/60">
              <Shield className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <p className="truncate text-[11px]">
                <strong className="text-gray-300 font-semibold">Подтверждено:</strong> {sourcesList.slice(0, 3).join(', ')}{sourcesList.length > 3 ? ` +${sourcesList.length - 3}` : ''}
              </p>
            </div>
          )}

          {/* ИИ ВЫЖИМКА */}
          {cleanInsight && (
            <div className="p-3 bg-gradient-to-r from-purple-950/20 via-blue-950/15 to-gray-900/40 rounded-xl border border-purple-500/20 mb-3 text-xs leading-relaxed">
              <div className="flex items-center gap-1.5 text-purple-400 font-bold text-[11px] mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>ИИ-анализ</span>
              </div>
              <p className="line-clamp-2 italic text-gray-300 text-[11px]">
                «{cleanInsight}»
              </p>
            </div>
          )}
        </div>

        {/* КНОПКА ПОЛНОГО РАЗБОРА (Всегда прибита к низу карточки) */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsModalOpen(true);
          }}
          className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-blue-600/20 via-indigo-600/25 to-blue-600/20 hover:from-blue-600/40 hover:to-indigo-600/40 text-blue-300 hover:text-white rounded-xl border border-blue-500/30 text-xs font-bold transition-all flex items-center justify-center gap-2 group-hover:border-blue-400/60 shadow-md"
        >
          <MessageSquare className="w-4 h-4 text-blue-400" />
          <span>Мысли капперов и полный разбор ({totalCappersCount})</span>
          <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

      {/* Модальное окно с детальным разбором */}
      {isModalOpen && (
        <MatchDetailModal bet={bet} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
};

export default TopBetCard;
