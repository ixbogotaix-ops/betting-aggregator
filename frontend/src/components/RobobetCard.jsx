import React from 'react';
import { Bot, Sparkles, Clock, Zap, ShieldCheck, ArrowRight, ExternalLink, CheckCircle2, XCircle, Flame } from 'lucide-react';
import TeamBadge from './TeamBadge';
import { toRussianTeam, toRussianLeague } from '../utils/russianNames';

const COUNTRY_MAP = {
  DZ: { name: 'Алжир', flag: 'https://flagcdn.com/w40/dz.png', emoji: '🇩🇿' },
  ES: { name: 'Испания', flag: 'https://flagcdn.com/w40/es.png', emoji: '🇪🇸' },
  EN: { name: 'Англия', flag: 'https://flagcdn.com/w40/gb-eng.png', emoji: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  GB: { name: 'Англия', flag: 'https://flagcdn.com/w40/gb-eng.png', emoji: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  IT: { name: 'Италия', flag: 'https://flagcdn.com/w40/it.png', emoji: '🇮🇹' },
  DE: { name: 'Германия', flag: 'https://flagcdn.com/w40/de.png', emoji: '🇩🇪' },
  FR: { name: 'Франция', flag: 'https://flagcdn.com/w40/fr.png', emoji: '🇫🇷' },
  RU: { name: 'Россия', flag: 'https://flagcdn.com/w40/ru.png', emoji: '🇷🇺' },
  PT: { name: 'Португалия', flag: 'https://flagcdn.com/w40/pt.png', emoji: '🇵🇹' },
  NL: { name: 'Нидерланды', flag: 'https://flagcdn.com/w40/nl.png', emoji: '🇳🇱' },
  TR: { name: 'Турция', flag: 'https://flagcdn.com/w40/tr.png', emoji: '🇹🇷' },
  BR: { name: 'Бразилия', flag: 'https://flagcdn.com/w40/br.png', emoji: '🇧🇷' },
  AR: { name: 'Аргентина', flag: 'https://flagcdn.com/w40/ar.png', emoji: '🇦🇷' },
  CL: { name: 'Чили', flag: 'https://flagcdn.com/w40/cl.png', emoji: '🇨🇱' },
  CO: { name: 'Колумбия', flag: 'https://flagcdn.com/w40/co.png', emoji: '🇨🇴' },
  MX: { name: 'Мексика', flag: 'https://flagcdn.com/w40/mx.png', emoji: '🇲🇽' },
  US: { name: 'США', flag: 'https://flagcdn.com/w40/us.png', emoji: '🇺🇸' },
  EG: { name: 'Египет', flag: 'https://flagcdn.com/w40/eg.png', emoji: '🇪🇬' },
  MA: { name: 'Марокко', flag: 'https://flagcdn.com/w40/ma.png', emoji: '🇲🇦' },
  TN: { name: 'Тунис', flag: 'https://flagcdn.com/w40/tn.png', emoji: '🇹🇳' },
  SA: { name: 'Саудовская Аравия', flag: 'https://flagcdn.com/w40/sa.png', emoji: '🇸🇦' },
  GR: { name: 'Греция', flag: 'https://flagcdn.com/w40/gr.png', emoji: '🇬🇷' },
  BE: { name: 'Бельгия', flag: 'https://flagcdn.com/w40/be.png', emoji: '🇧🇪' },
  SE: { name: 'Швеция', flag: 'https://flagcdn.com/w40/se.png', emoji: '🇸🇪' },
  PL: { name: 'Польша', flag: 'https://flagcdn.com/w40/pl.png', emoji: '🇵🇱' },
  CZ: { name: 'Чехия', flag: 'https://flagcdn.com/w40/cz.png', emoji: '🇨🇿' },
  AT: { name: 'Австрия', flag: 'https://flagcdn.com/w40/at.png', emoji: '🇦🇹' },
  CH: { name: 'Швейцария', flag: 'https://flagcdn.com/w40/ch.png', emoji: '🇨🇭' },
  UA: { name: 'Украина', flag: 'https://flagcdn.com/w40/ua.png', emoji: '🇺🇦' },
  KZ: { name: 'Казахстан', flag: 'https://flagcdn.com/w40/kz.png', emoji: '🇰🇿' },
  BY: { name: 'Беларусь', flag: 'https://flagcdn.com/w40/by.png', emoji: '🇧🇾' },
  ENGLAND: { name: 'Англия', flag: 'https://flagcdn.com/w40/gb-eng.png', emoji: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  SCOTLAND: { name: 'Шотландия', flag: 'https://flagcdn.com/w40/gb-sct.png', emoji: '🏴󠁧󠁢󠁳󠁣󠁴󠁿' },
  WALES: { name: 'Уэльс', flag: 'https://flagcdn.com/w40/gb-wls.png', emoji: '🏴󠁧󠁢󠁷󠁬󠁳󠁿' },
  SPAIN: { name: 'Испания', flag: 'https://flagcdn.com/w40/es.png', emoji: '🇪🇸' },
  GERMANY: { name: 'Германия', flag: 'https://flagcdn.com/w40/de.png', emoji: '🇩🇪' },
  ITALY: { name: 'Италия', flag: 'https://flagcdn.com/w40/it.png', emoji: '🇮🇹' },
  FRANCE: { name: 'Франция', flag: 'https://flagcdn.com/w40/fr.png', emoji: '🇫🇷' },
  RUSSIA: { name: 'Россия', flag: 'https://flagcdn.com/w40/ru.png', emoji: '🇷🇺' },
  PORTUGAL: { name: 'Португалия', flag: 'https://flagcdn.com/w40/pt.png', emoji: '🇵🇹' },
  NETHERLANDS: { name: 'Нидерланды', flag: 'https://flagcdn.com/w40/nl.png', emoji: '🇳🇱' },
  HOLLAND: { name: 'Нидерланды', flag: 'https://flagcdn.com/w40/nl.png', emoji: '🇳🇱' },
  BRAZIL: { name: 'Бразилия', flag: 'https://flagcdn.com/w40/br.png', emoji: '🇧🇷' },
  ARGENTINA: { name: 'Аргентина', flag: 'https://flagcdn.com/w40/ar.png', emoji: '🇦🇷' },
  TURKEY: { name: 'Турция', flag: 'https://flagcdn.com/w40/tr.png', emoji: '🇹🇷' },
  BELGIUM: { name: 'Бельгия', flag: 'https://flagcdn.com/w40/be.png', emoji: '🇧🇪' },
  ALGERIA: { name: 'Алжир', flag: 'https://flagcdn.com/w40/dz.png', emoji: '🇩🇿' },
  EU: { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  EUROPEANUNION: { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  'EUROPEAN UNION': { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  EUROPE: { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  UEFA: { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  'ЛИГА ЕВРОПЫ': { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  'ЛИГА ЕВРОПЫ УЕФА': { name: 'Лига Европы', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  'ЛИГА ЧЕМПИОНОВ': { name: 'Лига Чемпионов', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  'ЛИГА КОНФЕРЕНЦИЙ': { name: 'Лига Конференций', flag: 'https://flagcdn.com/w40/eu.png', emoji: '🇪🇺' },
  VE: { name: 'Венесуэла', flag: 'https://flagcdn.com/w40/ve.png', emoji: '🇻🇪' },
  VENEZUELA: { name: 'Венесуэла', flag: 'https://flagcdn.com/w40/ve.png', emoji: '🇻🇪' },
  WORLD: { name: 'Международные', flag: 'https://flagcdn.com/w40/un.png', emoji: '🌍' },
  INTERNATIONAL: { name: 'Международные', flag: 'https://flagcdn.com/w40/un.png', emoji: '🌍' },
  'МЕЖДУНАРОДНЫЕ': { name: 'Международные', flag: 'https://flagcdn.com/w40/un.png', emoji: '🌍' },
};

export const getCountryDisplay = (country = '', flagUrl = '', emoji = '') => {
  if (!country) return { name: 'Футбол', flag: null, emoji: '⚽' };
  const up = country.trim().toUpperCase();
  if (COUNTRY_MAP[up]) {
    return {
      name: COUNTRY_MAP[up].name,
      flag: flagUrl || COUNTRY_MAP[up].flag,
      emoji: emoji || COUNTRY_MAP[up].emoji
    };
  }
  return {
    name: country,
    flag: flagUrl || null,
    emoji: emoji || '🌍'
  };
};

const RobobetCard = ({ botd, onOpenRobobetTab }) => {
  if (!botd) return null;

  const team1 = toRussianTeam(botd.team1 || 'Команда 1');
  const team2 = toRussianTeam(botd.team2 || 'Команда 2');

  // Check outcome
  let isFinished = Boolean(botd.is_finished || (botd.score && botd.score !== '- : -' && botd.score.includes(':')));
  let isWin = botd.is_win;
  if (isWin === undefined || isWin === null) {
    if (botd.result_status === 'win') isWin = true;
    else if (botd.result_status === 'loss') isWin = false;
    else if (isFinished && botd.score && botd.score.includes(':')) {
      const parts = botd.score.split(':').map(s => parseInt(s.trim(), 10));
      if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        const [h, a] = parts;
        const rec = (botd.recommendation || '').toUpperCase().trim().replace('Х', 'X');
        if (rec === 'П1' || rec === 'P1') isWin = (h > a);
        else if (rec === 'П2' || rec === 'P2') isWin = (a > h);
        else if (rec === 'X' || rec === 'Х') isWin = (h === a);
        else if (rec === '1X') isWin = (h >= a);
        else if (rec === 'X2') isWin = (a >= h);
        else if (rec === '12') isWin = (h !== a);
      }
    }
  }

  return (
    <div 
      onClick={onOpenRobobetTab}
      className={`h-full flex flex-col justify-between rounded-3xl p-5 border-2 shadow-xl hover:shadow-2xl hover:-translate-y-1.5 cursor-pointer transition-all duration-300 relative overflow-hidden group select-none ${
        isFinished && isWin === true
          ? 'bg-gradient-to-b from-gray-900 via-emerald-950/20 to-gray-950 border-emerald-500/50 hover:border-emerald-400 hover:shadow-emerald-500/10'
          : isFinished && isWin === false
            ? 'bg-gradient-to-b from-gray-900 via-rose-950/20 to-gray-950 border-rose-500/40 hover:border-rose-400 hover:shadow-rose-500/10'
            : 'bg-gradient-to-b from-gray-900 via-purple-950/20 to-gray-950 border-purple-500/40 hover:border-purple-400 hover:shadow-purple-500/10'
      }`}
    >
      {/* Фоновое свечение в верхнем углу */}
      <div className={`absolute top-0 right-0 w-36 h-36 rounded-bl-full pointer-events-none blur-2xl transition-all ${
        isFinished && isWin === true
          ? 'bg-emerald-500/20 group-hover:bg-emerald-500/30'
          : isFinished && isWin === false
            ? 'bg-rose-500/20 group-hover:bg-rose-500/30'
            : 'bg-purple-500/15 group-hover:bg-purple-500/25'
      }`}></div>

      <div>
        {/* ВЕРХНЯЯ ШАПКА: Футбол СЛЕВА, Время/Статус СПРАВА */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-blue-500/20 to-indigo-500/10 rounded-full text-xs font-black border border-blue-500/30 text-blue-300 shadow-sm shrink-0">
              <span className="text-sm">⚽</span>
              <span className="truncate max-w-[140px] uppercase text-[11px] tracking-wider font-extrabold">
                ФУТБОЛ
              </span>
            </span>
          </div>

          {isFinished && isWin === true ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/20 rounded-xl border border-emerald-500/50 text-xs font-black text-emerald-300 shrink-0 shadow-sm shadow-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span className="whitespace-nowrap font-mono">{botd.score}</span>
              <span className="text-[10px] text-emerald-400 font-black uppercase tracking-wider">ПРОШЕЛ</span>
            </div>
          ) : isFinished && isWin === false ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-500/20 rounded-xl border border-rose-500/50 text-xs font-black text-rose-300 shrink-0 shadow-sm shadow-rose-500/20">
              <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
              <span className="whitespace-nowrap font-mono">{botd.score}</span>
              <span className="text-[10px] text-rose-400 font-black uppercase tracking-wider">НЕ ЗАШЕЛ</span>
            </div>
          ) : (botd.match_status_label === 'live' || (botd.is_time_past && !isFinished)) ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-500/25 rounded-xl border border-rose-500/60 text-xs font-black text-rose-300 shrink-0 shadow-sm shadow-rose-500/20 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              <span className="whitespace-nowrap font-mono">{botd.time}</span>
              <span className="text-[10px] text-rose-400 font-black uppercase tracking-wider">МАТЧ ИДЕТ</span>
            </div>
          ) : botd.time ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-950/90 rounded-xl border border-gray-700/80 text-xs font-black text-gray-200 shrink-0 shadow-inner">
              <Clock className="w-3.5 h-3.5 text-purple-400 shrink-0" />
              <span className="whitespace-nowrap font-mono">{botd.time}</span>
              <span className="text-[10px] text-purple-400 font-black uppercase tracking-wider">МСК</span>
            </div>
          ) : null}
        </div>

        {/* ПОДШАПКА: Статус "Ставка Дня Робобет" + Страна/Турнир + Консенсус */}
        <div className="flex items-center gap-2 flex-wrap mb-4">
          <span className="inline-flex items-center gap-1.5 text-[11px] font-black text-purple-300 bg-purple-500/20 px-2.5 py-0.5 rounded-lg border border-purple-400/50 shadow-sm animate-pulse">
            <Bot className="w-3.5 h-3.5 text-purple-300" />
            <span>СТАВКА ДНЯ</span>
            <span className="text-purple-400/60">•</span>
            <span className="text-purple-200 font-semibold">РОБОБЕТ ИИ</span>
          </span>

          {botd.is_triple_consensus ? (
            <span className="text-[10px] font-black text-rose-300 bg-rose-500/25 px-2.5 py-0.5 rounded-md border border-rose-500/50 flex items-center gap-1 shadow-sm animate-pulse">
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>СУПЕР ИИ 3/3</span>
            </span>
          ) : botd.is_math_consensus ? (
            <span className="text-[10px] font-black text-amber-300 bg-amber-500/20 px-2 py-0.5 rounded-md border border-amber-500/40 flex items-center gap-1 shadow-sm">
              <Sparkles className="w-3 h-3 text-amber-400" />
              <span>Консенсус 2-х ИИ</span>
            </span>
          ) : null}

          {botd.country && (() => {
            const tournamentName = toRussianLeague(botd.country);
            const cDisplay = getCountryDisplay(botd.country, botd.country_flag_url, botd.country_emoji);
            return (
              <span className="text-xs font-bold text-gray-300 px-3 py-1 bg-gray-800/80 rounded-lg border border-gray-750 truncate max-w-[220px] inline-flex items-center gap-1.5 shadow-sm" title={tournamentName}>
                {cDisplay.flag ? (
                  <img 
                    src={cDisplay.flag} 
                    alt="" 
                    className="w-4 h-3 object-cover rounded-[2px] opacity-85 shrink-0" 
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                ) : (
                  <span>{cDisplay.emoji}</span>
                )}
                <span className="truncate">{tournamentName}</span>
              </span>
            );
          })()}

          {botd.vitibet_proj_score && (
            <span className="text-[10px] font-bold text-blue-300 bg-blue-950/60 px-2 py-0.5 rounded-md border border-blue-800/60 font-mono">
              🎯 Счёт: {botd.vitibet_proj_score}
            </span>
          )}

          {botd.has_zulubet && (
            <span className="text-[10px] font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded-md border border-cyan-800/60 font-mono" title={`Zulubet: 1(${botd.zulubet_prob_1}%) X(${botd.zulubet_prob_x}%) 2(${botd.zulubet_prob_2}%)`}>
              🤖 Zulu: {botd.zulubet_tip}
            </span>
          )}

          {botd.is_value && (
            <span className="text-[10px] font-black text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-md border border-emerald-500/30">
              +EV {Math.round(botd.ev * 100)}%
            </span>
          )}
        </div>

        {/* БЛОК ПРОТИВОСТОЯНИЯ (Эмблемы и Крупные жирные Названия) */}
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 p-3.5 bg-gray-950/60 rounded-2xl border border-gray-800/80 mb-4 shadow-inner">
          {/* Хозяева */}
          <div className="flex flex-col items-center text-center">
            <TeamBadge teamName={team1} logoUrl={botd.home_logo} size="lg" className="mb-2.5" />
            <span className="text-base sm:text-lg font-black text-white leading-snug min-h-[3rem] flex items-center justify-center line-clamp-2 px-1 tracking-tight text-center drop-shadow-md font-heading hover:text-purple-300 transition-colors">
              {team1}
            </span>
            <span className="text-[11px] text-gray-400 font-bold mt-0.5 uppercase tracking-wider">Хозяева</span>
          </div>

          {/* Разделитель VS */}
          <div className="flex flex-col items-center justify-center px-1">
            <span className="w-8 h-8 rounded-full bg-purple-950/90 border border-purple-700/60 flex items-center justify-center text-xs font-black text-purple-300 italic shadow-inner font-heading">
              VS
            </span>
          </div>

          {/* Гости */}
          <div className="flex flex-col items-center text-center">
            <TeamBadge teamName={team2} logoUrl={botd.away_logo} size="lg" className="mb-2.5" />
            <span className="text-base sm:text-lg font-black text-white leading-snug min-h-[3rem] flex items-center justify-center line-clamp-2 px-1 tracking-tight text-center drop-shadow-md font-heading hover:text-purple-300 transition-colors">
              {team2}
            </span>
            <span className="text-[11px] text-gray-400 font-bold mt-0.5 uppercase tracking-wider">Гости</span>
          </div>
        </div>

        {/* ШКАЛА ВЕРОЯТНОСТЕЙ ДИСОНА-КОУЛЗА */}
        <div className="mb-4 bg-gray-950/50 p-2.5 rounded-2xl border border-gray-800/70">
          <div className="flex items-center justify-between text-[11px] font-bold text-gray-400 mb-1.5">
            <span className="text-emerald-400">П1: {botd.prob_1}%</span>
            <span className="text-amber-400">Ничья: {botd.prob_x}%</span>
            <span className="text-blue-400">П2: {botd.prob_2}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-gray-800 overflow-hidden flex border border-gray-700/60">
            <div style={{ width: `${botd.prob_1}%` }} className="bg-emerald-500 h-full" title={`П1: ${botd.prob_1}%`}></div>
            <div style={{ width: `${botd.prob_x}%` }} className="bg-amber-500 h-full" title={`X: ${botd.prob_x}%`}></div>
            <div style={{ width: `${botd.prob_2}%` }} className="bg-blue-500 h-full" title={`П2: ${botd.prob_2}%`}></div>
          </div>
        </div>

        {/* РЕКОМЕНДОВАННЫЙ ПРОГНОЗ */}
        <div className="p-3.5 bg-purple-950/30 border border-purple-500/30 rounded-2xl mb-4 group-hover:border-purple-400/50 transition-colors">
          <div className="text-[10px] font-bold uppercase text-purple-300 tracking-wider mb-1 flex items-center justify-between">
            <span>Рекомендация Робобета</span>
            <span className="text-emerald-400 font-black flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Шанс {botd.rec_prob}%</span>
            </span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <div className="font-black text-white text-base sm:text-lg">
              Исход: <span className="text-amber-300 font-mono">{botd.recommendation}</span>
            </div>
            <div className="flex items-center gap-1.5 bg-gray-900/90 px-3 py-1 rounded-xl border border-gray-700">
              <span className="text-[10px] text-gray-400 font-bold uppercase">Кэф</span>
              <span className="font-mono font-black text-amber-400 text-sm">
                {botd.rec_odd ? Number(botd.rec_odd).toFixed(2) : '-'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* НИЖНЯЯ ПЛАШКА: Ссылка на раздел Робобет */}
      <div className="pt-3 border-t border-gray-800/80 flex items-center justify-between text-xs text-purple-300 font-bold group-hover:text-purple-200 transition-colors">
        <span className="flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5 text-purple-400" />
          <span>Математический ИИ-расчёт</span>
        </span>
        <div className="flex items-center gap-1 text-purple-400 group-hover:translate-x-1 transition-transform">
          <span>Смотреть все матчи</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </div>
  );
};

export default RobobetCard;
