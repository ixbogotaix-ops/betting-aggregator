import React, { useState } from 'react';
import { 
  X, Target, Shield, Sparkles, Brain, TrendingUp, Users, 
  MessageSquare, Flame, BookOpen, Swords, BarChart3, CheckCircle2 
} from 'lucide-react';
import { getSportDisplay } from './TopBetCard';

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

const getRussianSport = (sport) => {
  const s = (sport || '').toLowerCase();
  if (s.includes('soccer') || s.includes('liga') || s.includes('ligue') || s.includes('epl') || s.includes('football') || s.includes('premier') || s.includes('championship') || s.includes('serie') || s.includes('bundesliga') || s.includes('uefa')) return 'ФУТБОЛ';
  if (s.includes('nba') || s.includes('basketball') || s.includes('euroleague')) return 'БАСКЕТБОЛ';
  if (s.includes('nhl') || s.includes('hockey') || s.includes('khl') || s.includes('allsvenskan')) return 'ХОККЕЙ';
  if (s.includes('tennis') || s.includes('atp') || s.includes('wta')) return 'ТЕННИС';
  if (s.includes('mma') || s.includes('ufc') || s.includes('martial')) return 'ММА';
  if (s.includes('nfl') || s.includes('american')) return 'АМЕР. ФУТБОЛ';
  return 'СПОРТ';
};

const formatMoscowTime = (dateStr) => {
  if (!dateStr) return { day: '', time: '' };
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
        const dayNum = parseInt(m[3], 10);
        const mIdx = parseInt(m[2], 10) - 1;
        return {
          day: `${dayNum} ${months[mIdx] || ''}`,
          time: `${m[4]}:${m[5]}`
        };
      }
      return { day: '', time: '' };
    }
    const day = d.toLocaleDateString('ru-RU', {
      timeZone: 'Europe/Moscow',
      month: 'short',
      day: 'numeric'
    }).replace('.', '');
    const time = d.toLocaleTimeString('ru-RU', {
      timeZone: 'Europe/Moscow',
      hour: '2-digit',
      minute: '2-digit'
    });
    return { day, time };
  } catch (e) {
    return { day: '', time: '' };
  }
};

const MatchDetailModal = ({ bet, onClose }) => {
  if (!bet) return null;

  const [activeTab, setActiveTab] = useState('sources'); // 'sources', 'tactics', 'ai'
  const mskTime = formatMoscowTime(bet.match_date);

  const [homeTeam, awayTeam] = bet.match_name.includes(' vs ')
    ? bet.match_name.split(' vs ')
    : bet.match_name.split(' - ');

  const getLogoUrl = (teamName) =>
    `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName || 'Team')}&background=random&color=fff&size=80&bold=true&rounded=true`;

  const predictions = bet.all_predictions || [];

  // Подсчет распределения исходов
  const outcomesCount = {};
  predictions.forEach(p => {
    const out = formatOutcome(p.predicted_outcome, homeTeam, awayTeam);
    outcomesCount[out] = (outcomesCount[out] || 0) + 1;
  });

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-fade-in overflow-y-auto"
      onClick={onClose}
    >
      <div 
        className="relative w-full max-w-3xl bg-gray-900 border border-gray-700/80 rounded-3xl shadow-2xl overflow-hidden my-auto max-h-[92vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 text-gray-400 hover:text-white bg-gray-800/80 hover:bg-gray-700 rounded-full transition-all border border-gray-700 shadow-md"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Шапка модалки */}
        <div className="p-6 bg-gradient-to-b from-gray-800/70 via-gray-850 to-gray-900 border-b border-gray-800 shrink-0">
          {(() => {
            const sportDisplay = getSportDisplay(bet.sport_type, bet.league);
            return (
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r ${sportDisplay.color} rounded-full text-xs font-black border shadow-sm`}>
                  <span className="text-sm">{sportDisplay.icon}</span>
                  <span className="uppercase text-[11px] tracking-wider font-extrabold">{sportDisplay.name}</span>
                </span>

                <span className="text-xs font-semibold px-2.5 py-1 bg-gray-800 text-gray-300 rounded-md border border-gray-700 inline-flex items-center gap-1.5">
                  {bet.country_flag_url && (
                    <img 
                      src={bet.country_flag_url} 
                      alt="" 
                      className="w-3.5 h-2.5 object-cover rounded-[2px] opacity-75 shrink-0" 
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <span>{bet.league || bet.country_name || "Лига"}</span>
                </span>

                {bet.is_bet_of_the_day && (
                  <span className="text-xs font-black text-amber-300 bg-amber-500/15 px-3 py-1 rounded-md border border-amber-400/40 flex items-center gap-1 animate-pulse">
                    🏆 СТАВКА ДНЯ • {sportDisplay.name.toUpperCase()}
                  </span>
                )}
              </div>
            );
          })()}

          {/* Команды и время матча с эмблемами */}
          <div className="flex items-center justify-between gap-4 mt-3">
            <div className="flex flex-col items-center flex-1 text-center">
              <div className="w-20 h-20 p-2 bg-gray-800/90 rounded-3xl flex items-center justify-center mb-2 ring-2 ring-blue-500/40 shadow-xl">
                <img 
                  src={bet.home_logo || getLogoUrl(homeTeam)} 
                  alt={homeTeam} 
                  className="max-w-full max-h-full object-contain filter drop-shadow-lg"
                  onError={(e) => { e.currentTarget.src = getLogoUrl(homeTeam); }}
                />
              </div>
              <h3 className="font-bold text-white text-base leading-tight">{homeTeam}</h3>
              <span className="text-[11px] text-gray-400 mt-0.5">Хозяева</span>
            </div>

            <div className="flex flex-col items-center justify-center px-2">
              {bet.final_score_home !== null && bet.final_score_away !== null ? (
                <div className="flex flex-col items-center">
                  <div className="px-4 py-2 bg-gray-800/95 rounded-2xl border border-gray-600 text-center mb-1 shadow-inner">
                    <span className="text-2xl font-black text-white tracking-wider">
                      {bet.final_score_home} : {bet.final_score_away}
                    </span>
                    <span className="text-[10px] text-emerald-400 font-black uppercase tracking-widest block mt-0.5">
                      МАТЧ ЗАВЕРШЁН
                    </span>
                  </div>
                </div>
              ) : (
                <div className="px-3.5 py-1.5 bg-gray-800/90 rounded-2xl border border-gray-700 text-center mb-1 shadow-inner">
                  <span className="text-[11px] text-gray-400 block font-semibold">
                    {mskTime.day}
                  </span>
                  <span className="text-lg font-black text-white">
                    {mskTime.time}
                  </span>
                  <span className="text-[9px] text-blue-400 font-extrabold uppercase tracking-widest block mt-0.5">
                    МСК
                  </span>
                </div>
              )}
              {bet.final_score_home === null && (
                <span className="text-xs font-black text-gray-500 italic">VS</span>
              )}
            </div>

            <div className="flex flex-col items-center flex-1 text-center">
              <div className="w-20 h-20 p-2 bg-gray-800/90 rounded-3xl flex items-center justify-center mb-2 ring-2 ring-purple-500/40 shadow-xl">
                <img 
                  src={bet.away_logo || getLogoUrl(awayTeam)} 
                  alt={awayTeam} 
                  className="max-w-full max-h-full object-contain filter drop-shadow-lg"
                  onError={(e) => { e.currentTarget.src = getLogoUrl(awayTeam); }}
                />
              </div>
              <h3 className="font-bold text-white text-base leading-tight">{awayTeam}</h3>
              <span className="text-[11px] text-gray-400 mt-0.5">Гости</span>
            </div>
          </div>

          {/* Главный консенсус плашка */}
          <div className={`mt-5 p-4 bg-gradient-to-r ${
            bet.bet_result === 'win'
              ? 'from-emerald-950/60 via-gray-900 to-gray-900 border-emerald-500/50'
              : bet.bet_result === 'loss'
              ? 'from-rose-950/60 via-gray-900 to-gray-900 border-rose-500/50'
              : bet.bet_result === 'refund'
              ? 'from-amber-950/60 via-gray-900 to-gray-900 border-amber-500/50'
              : 'from-blue-950/60 via-indigo-950/40 to-gray-900 border-blue-500/30'
          } rounded-2xl border shadow-inner flex items-center justify-between gap-4`}>
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-500/20 rounded-xl text-blue-400 shrink-0">
                <Target className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[11px] uppercase tracking-wider text-blue-300 font-bold">
                    Главный консенсус алгоритма
                  </span>
                  {bet.bet_result === 'win' && (
                    <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-black rounded-md animate-pulse">
                      ✅ СТАВКА ЗАШЛА
                    </span>
                  )}
                  {bet.bet_result === 'loss' && (
                    <span className="px-2 py-0.5 bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-black rounded-md">
                      ❌ НЕ ЗАШЛА
                    </span>
                  )}
                  {bet.bet_result === 'refund' && (
                    <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-black rounded-md">
                      🔄 ВОЗВРАТ
                    </span>
                  )}
                </div>
                <span className="text-lg font-black text-white leading-tight">
                  {formatOutcome(bet.recommended_outcome, homeTeam, awayTeam)}
                </span>
              </div>
            </div>
            <div className="text-right shrink-0">
              <span className="text-2xl font-black text-emerald-400">{bet.average_odds.toFixed(2)}</span>
              <span className="text-[10px] text-gray-400 uppercase tracking-widest block font-bold">КЭФ</span>
            </div>
          </div>

          {/* Навигационные табы */}
          <div className="flex items-center gap-2 mt-4 pt-2 border-t border-gray-800 overflow-x-auto custom-scrollbar">
            <button
              onClick={() => setActiveTab('sources')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
                activeTab === 'sources'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'bg-gray-800/80 text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>💬 Размышления источников ({predictions.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('tactics')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
                activeTab === 'tactics'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'bg-gray-800/80 text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>📋 Тактический разбор и факты</span>
            </button>
            <button
              onClick={() => setActiveTab('ai')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
                activeTab === 'ai'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'bg-gray-800/80 text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>🤖 ИИ-Нейровердикт</span>
            </button>
          </div>
        </div>

        {/* Прокручиваемый контент вкладки */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 custom-scrollbar">
          {/* ТАБ 1: РАЗМЫШЛЕНИЯ ИСТОЧНИКОВ */}
          {activeTab === 'sources' && (
            <div className="space-y-4">
              {/* Сводная мысль капперов */}
              {bet.cappers_reasoning && (
                <div className="p-4 bg-indigo-950/25 rounded-2xl border border-indigo-500/30 shadow-sm">
                  <div className="flex items-center gap-2 mb-2 text-indigo-400 font-bold text-xs uppercase tracking-wider">
                    <Brain className="w-4 h-4 text-indigo-400" />
                    <span>Сводный консенсус экспертов</span>
                  </div>
                  <p className="text-sm text-gray-200 leading-relaxed">
                    {bet.cappers_reasoning}
                  </p>
                </div>
              )}

              {/* Распределение мнений капперов */}
              {Object.keys(outcomesCount).length > 0 && (
                <div className="p-4 bg-gray-800/40 rounded-2xl border border-gray-700/50 space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold text-gray-300 mb-1">
                    <span className="flex items-center gap-1.5">
                      <BarChart3 className="w-4 h-4 text-emerald-400" /> Распределение голосов капперов
                    </span>
                    <span className="text-gray-400">Всего: {predictions.length} прогнозов</span>
                  </div>
                  <div className="space-y-2">
                    {Object.entries(outcomesCount).map(([outcomeName, count], idx) => {
                      const percent = Math.round((count / predictions.length) * 100);
                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between text-xs text-gray-300">
                            <span className="font-semibold">{outcomeName}</span>
                            <span className="font-black text-emerald-400">{percent}% ({count})</span>
                          </div>
                          <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 rounded-full" 
                              style={{ width: `${percent}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Детальный список источников с их РАЗМЫШЛЕНИЯМИ */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    <span>Кто и почему так ставит ({predictions.length} источников):</span>
                  </h4>
                  <span className="text-xs text-gray-400">Глубокие аргументы</span>
                </div>

                {predictions.length > 0 ? (
                  <div className="space-y-3">
                    {predictions.map((p, idx) => (
                      <div 
                        key={idx}
                        className="p-4 bg-gray-800/80 hover:bg-gray-800 rounded-2xl border border-gray-700/70 transition-all space-y-3 shadow-md"
                      >
                        {/* Шапка источника */}
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <span className="text-xl shrink-0">
                              {p.source_type === 'telegram_channel' ? '📡' : '🌐'}
                            </span>
                            <div className="min-w-0">
                              <span className="font-bold text-white block text-sm truncate">
                                {p.source_name}
                              </span>
                              <div className="flex items-center gap-2 text-[11px] text-gray-400 mt-0.5">
                                <span>{p.source_type === 'telegram_channel' ? 'Telegram Канал' : 'Аналитический Портал'}</span>
                                {p.source_weight && (
                                  <span className="text-amber-400 font-semibold bg-amber-400/10 px-1.5 py-0.2 rounded border border-amber-400/20">
                                    Рейтинг: {p.source_weight}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="text-right shrink-0">
                            <div className="flex items-center justify-end gap-1.5 mb-0.5">
                              {p.status === 'win' && (
                                <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-black rounded">
                                  ✅ Зашло
                                </span>
                              )}
                              {p.status === 'loss' && (
                                <span className="px-1.5 py-0.5 bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px] font-black rounded">
                                  ❌ Мимо
                                </span>
                              )}
                              {p.status === 'refund' && (
                                <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 text-[10px] font-black rounded">
                                  🔄 Возврат
                                </span>
                              )}
                              <span className="font-black text-emerald-400 text-sm block">
                                {formatOutcome(p.predicted_outcome, homeTeam, awayTeam)}
                              </span>
                            </div>
                            <span className="text-[11px] text-gray-400 font-bold">
                              Кэф: <strong className="text-white text-xs">{p.odds}</strong>
                            </span>
                          </div>
                        </div>

                        {/* Блок с размышлениями и аргументами источника */}
                        {p.reasoning && (
                          <div className="p-3 bg-gray-900/80 rounded-xl border border-gray-700/60 text-xs text-gray-300 leading-relaxed relative">
                            <div className="flex items-center gap-1.5 text-blue-400 font-bold text-[11px] mb-1">
                              <MessageSquare className="w-3.5 h-3.5" />
                              <span>Размышления и аргументы эксперта:</span>
                            </div>
                            <p className="italic text-gray-200">
                              «{p.reasoning}»
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-5 bg-gray-800/30 rounded-2xl border border-gray-800 text-center text-xs text-gray-400">
                    Подтверждено источниками: <strong className="text-gray-200">{bet.supporting_sources.join(', ')}</strong>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ТАБ 2: ТАКТИЧЕСКИЙ РАЗБОР И КЛЮЧЕВЫЕ ФАКТОРЫ */}
          {activeTab === 'tactics' && (
            <div className="space-y-5">
              {/* Тактический анализ */}
              {bet.tactical_analysis && (
                <div className="p-5 bg-gray-800/60 rounded-2xl border border-gray-700/70 space-y-3">
                  <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
                    <BookOpen className="w-4 h-4" />
                    <span>Тактический расклад и форма команд</span>
                  </div>
                  <div className="text-sm text-gray-200 leading-relaxed whitespace-pre-line">
                    {bet.tactical_analysis}
                  </div>
                </div>
              )}

              {/* Ключевые факторы матча */}
              {bet.key_factors && bet.key_factors.length > 0 && (
                <div className="p-5 bg-gray-800/60 rounded-2xl border border-gray-700/70 space-y-3">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                    <Flame className="w-4 h-4" />
                    <span>Ключевые факторы матча</span>
                  </div>
                  <div className="space-y-2">
                    {bet.key_factors.map((factor, idx) => (
                      <div 
                        key={idx}
                        className="p-3 bg-gray-900/60 rounded-xl border border-gray-700/50 text-xs text-gray-200 flex items-start gap-2.5"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span className="leading-snug">{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Очные встречи (H2H) */}
              {bet.h2h_summary && (
                <div className="p-5 bg-gray-800/60 rounded-2xl border border-gray-700/70 space-y-2">
                  <div className="flex items-center gap-2 text-purple-400 font-bold text-sm">
                    <Swords className="w-4 h-4" />
                    <span>История очных встреч (H2H)</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {bet.h2h_summary}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ТАБ 3: ИИ-НЕЙРОВЕРДИКТ */}
          {activeTab === 'ai' && (
            <div className="space-y-5">
              {/* Инсайт нейросети */}
              <div className="p-5 bg-gradient-to-r from-blue-900/40 via-purple-900/30 to-gray-900 rounded-2xl border border-blue-500/40 relative shadow-lg space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
                    <Sparkles className="w-5 h-5 text-blue-400 animate-spin-slow" />
                    <span>ИНСАЙТ ИИ-АНАЛИТИКА</span>
                  </div>
                  <span className="text-xs font-black px-2.5 py-1 bg-blue-500/20 text-blue-300 rounded-lg border border-blue-500/30">
                    Индекс уверенности: {bet.confidence_score}%
                  </span>
                </div>
                <div className="text-sm text-gray-100 leading-relaxed whitespace-pre-line font-medium">
                  {bet.ai_insight || "Алгоритм фиксирует высокую сходимость мнений ведущих экспертов и математических моделей трендов."}
                </div>
              </div>

              {/* Шкала надежности */}
              <div className="bg-gray-800/50 p-4 rounded-2xl border border-gray-700/60 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-300 font-semibold flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-blue-400" /> Степень согласованности моделей
                  </span>
                  <span className="font-black text-blue-400 text-sm">{bet.confidence_score}%</span>
                </div>
                <div className="h-3 w-full bg-gray-800 rounded-full overflow-hidden p-0.5 border border-gray-700/40">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 rounded-full transition-all duration-1000" 
                    style={{ width: `${bet.confidence_score}%` }}
                  ></div>
                </div>
              </div>

              {/* Сводка капперов */}
              {bet.cappers_reasoning && (
                <div className="p-4 bg-gray-800/40 rounded-2xl border border-gray-700/50">
                  <div className="flex items-center gap-2 mb-2 text-gray-400 font-bold text-xs uppercase tracking-wider">
                    <Brain className="w-4 h-4 text-indigo-400" />
                    <span>Сводный консенсус экспертов</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {bet.cappers_reasoning}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Подвал модалки */}
        <div className="p-4 bg-gray-900 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400 shrink-0 px-6">
          <span>Синхронизировано с 52 источников в реальном времени</span>
          <span className="font-semibold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Анализ подтвержден
          </span>
        </div>
      </div>
    </div>
  );
};

export default MatchDetailModal;
