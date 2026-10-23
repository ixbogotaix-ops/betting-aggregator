import React, { useState, useEffect, useRef } from 'react';
import { 
  Trophy, CheckCircle2, XCircle, RotateCcw, TrendingUp, 
  Calendar, ChevronLeft, ChevronRight, ChevronDown, 
  Sparkles, Bot, ShieldCheck, Flame, BarChart3, 
  Layers, ArrowUpRight, Check, Activity, Clock, ArrowRight,
  ExternalLink, ChevronUp
} from 'lucide-react';
import { getMonthlyPerformance } from '../api';
import { toRussianTeam } from '../utils/russianNames';

export default function MonthlyPerformanceWidget({ todayBotd = null, todayRobobet = null }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(null); // 'YYYY-MM' or null for current
  const [activeMode, setActiveMode] = useState('botd'); // 'botd' | 'robobet'
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isMobileExpanded, setIsMobileExpanded] = useState(false);
  const dropdownRef = useRef(null);
  const daysListRef = useRef(null);

  // Закрытие дропдауна при клике вне
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Загрузка статистики
  const fetchStats = async (monthVal, modeVal) => {
    setLoading(true);
    try {
      const res = await getMonthlyPerformance(monthVal, modeVal);
      if (res) {
        setData(res);
        if (!selectedMonth) {
          setSelectedMonth(res.selected_month);
        }
        // При смене месяца плавно прокручиваем список дней наверх
        if (daysListRef.current) {
          daysListRef.current.scrollTop = 0;
        }
      }
    } catch (err) {
      console.error("Ошибка загрузки ежемесячной статистики:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats(selectedMonth, activeMode);
  }, [selectedMonth, activeMode]);

  if (!data && loading) {
    return (
      <div className="w-full bg-gradient-to-br from-card via-[#131b2e] to-[#0c1220] rounded-3xl border border-gray-800 p-5 shadow-xl animate-pulse">
        <div className="h-6 bg-gray-800 rounded-lg w-48 mb-4"></div>
        <div className="h-20 bg-gray-800/60 rounded-2xl mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-14 bg-gray-800/40 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { 
    selected_month, 
    selected_month_label, 
    is_current_month, 
    today_day,
    available_months, 
    current_month_to_date, 
    selected_month_summary, 
    all_time_summary, 
    days 
  } = data;

  const currentMonthIdx = available_months.findIndex(m => m.value === selected_month);
  const canGoPrev = currentMonthIdx < available_months.length - 1;
  const canGoNext = currentMonthIdx > 0;

  const handlePrevMonth = () => {
    if (canGoPrev) setSelectedMonth(available_months[currentMonthIdx + 1].value);
  };

  const handleNextMonth = () => {
    if (canGoNext) setSelectedMonth(available_months[currentMonthIdx - 1].value);
  };

  return (
    <div className="w-full bg-gradient-to-br from-card via-[#12192c] to-[#0b101c] rounded-3xl border border-blue-500/25 p-4 sm:p-5 shadow-2xl shadow-blue-950/20 text-white">
      {/* 1. Верхняя панель: Заголовок и выбор месяца */}
      <div className="flex items-center justify-between gap-2 pb-3.5 border-b border-gray-800/80">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-gradient-to-tr from-blue-600 to-cyan-500 rounded-lg text-white shadow-md shadow-blue-500/20">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-black font-heading text-white tracking-tight flex items-center gap-1.5">
              <span>Трек-рекорд по дням</span>
              {is_current_month && (
                <span className="px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full animate-pulse">
                  Live
                </span>
              )}
            </h3>
            <p className="text-[11px] text-gray-400">
              Строго 1 главная ставка на каждый день
            </p>
          </div>
        </div>

        {/* Навигатор месяцев: [◀] [ Октябрь ▼ ] [▶] */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={handlePrevMonth}
            disabled={!canGoPrev || loading}
            title="Предыдущий месяц"
            className="p-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 border border-gray-700/70 text-gray-300 hover:text-white transition-all disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>

          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-gray-900/90 hover:bg-gray-800 border border-blue-500/40 text-white font-bold text-xs transition-all"
            >
              <span>{selected_month_label.split(' ')[0]}</span>
              <ChevronDown className={`w-3 h-3 text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {isDropdownOpen && (
              <div className="absolute right-0 mt-1.5 w-48 max-h-64 overflow-y-auto custom-scrollbar bg-gray-900/95 backdrop-blur-xl border border-gray-700 rounded-xl shadow-2xl p-1 z-50 animate-fade-in">
                <div className="px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider text-gray-400 border-b border-gray-800 mb-1">
                  Месяцы
                </div>
                {available_months.map((m) => {
                  const isSel = m.value === selected_month;
                  return (
                    <button
                      key={m.value}
                      onClick={() => {
                        setSelectedMonth(m.value);
                        setIsDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        isSel ? 'bg-blue-600 text-white' : 'text-gray-300 hover:text-white hover:bg-gray-800/70'
                      }`}
                    >
                      <span>{m.label}</span>
                      {isSel && <Check className="w-3 h-3" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <button
            onClick={handleNextMonth}
            disabled={!canGoNext || loading}
            title="Следующий месяц"
            className="p-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 border border-gray-700/70 text-gray-300 hover:text-white transition-all disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Переключатель режима: Ставка Дня / Робобет */}
      <div className="grid grid-cols-2 gap-1.5 p-1 bg-gray-900/80 rounded-xl border border-gray-800 my-3">
        <button
          onClick={() => setActiveMode('botd')}
          className={`py-1.5 px-2 rounded-lg font-black text-xs transition-all flex items-center justify-center gap-1.5 ${
            activeMode === 'botd'
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/30'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-300" />
          <span>👑 Ставка Дня</span>
        </button>

        <button
          onClick={() => setActiveMode('robobet')}
          className={`py-1.5 px-2 rounded-lg font-black text-xs transition-all flex items-center justify-center gap-1.5 ${
            activeMode === 'robobet'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-600/30'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          <Bot className="w-3.5 h-3.5 text-cyan-300" />
          <span>🤖 Робобет ИИ</span>
        </button>
      </div>

      {/* 3. Двойная сводка: Текущий месяц M-T-D + Вообще за ВСЕ месяцы */}
      <div className="space-y-2 mb-3.5">
        {/* Карточка 1: На сегодняшний день (Октябрь 1..17) */}
        <div className="p-3 rounded-2xl bg-gradient-to-br from-blue-950/40 via-gray-900 to-gray-900/90 border border-blue-500/30 shadow-md">
          <div className="flex items-center justify-between text-[11px] font-bold text-gray-300 mb-1.5">
            <span className="flex items-center gap-1 text-blue-400">
              <Calendar className="w-3 h-3" />
              <span>За октябрь (на {today_day} окт):</span>
            </span>
            <span className="text-[10px] text-gray-400">
              {current_month_to_date.total_days} {current_month_to_date.total_days === 1 ? 'ставка' : 'ставок'}
            </span>
          </div>

          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-black text-xs flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>{current_month_to_date.wins} прошло</span>
              </span>
              <span className="px-2 py-0.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 font-black text-xs flex items-center gap-1">
                <XCircle className="w-3 h-3" />
                <span>{current_month_to_date.losses} мимо</span>
              </span>
            </div>

            <div className="text-right">
              <div className="text-sm font-black text-cyan-400 font-heading">
                {current_month_to_date.winrate}%
              </div>
              <div className="text-[10px] font-bold text-emerald-400">
                +{current_month_to_date.profit_units} флэт
              </div>
            </div>
          </div>
        </div>

        {/* Карточка 2: Вообще за ВСЕ месяцы (All-Time) */}
        <div className="p-2.5 rounded-xl bg-gray-900/70 border border-gray-800 hover:border-gray-700/80 transition-all flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="p-1 rounded-md bg-amber-500/15 text-amber-400">
              <Trophy className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-[11px] font-black text-gray-200">Итого за все месяцы:</div>
              <div className="text-[10px] text-gray-400">
                {all_time_summary.total_bets} ставок • {all_time_summary.wins} ✅ / {all_time_summary.losses} ❌
              </div>
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs font-black text-emerald-400">
              {all_time_summary.winrate}%
            </span>
            <span className="text-[10px] text-gray-400 block font-semibold">
              +{all_time_summary.profit_units} флэт
            </span>
          </div>
        </div>
      </div>

      {/* Мобильная кнопка разворачивания списка дней */}
      <div className="block lg:hidden mb-2">
        <button
          onClick={() => setIsMobileExpanded(!isMobileExpanded)}
          className="w-full py-2 px-3 rounded-xl bg-gray-900 border border-gray-800 text-xs font-bold text-blue-400 flex items-center justify-between"
        >
          <span>{isMobileExpanded ? 'Скрыть список матчей по дням' : `Развернуть дни (${days.length} ставок) ▼`}</span>
          {isMobileExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* 4. СПИСОК МАТЧЕЙ ПО ДНЯМ (В СТОЛБИК, ТОЛЬКО СТАВКА ДНЯ) */}
      <div className={`${isMobileExpanded ? 'block' : 'hidden'} lg:block`}>
        <div className="flex items-center justify-between text-[11px] font-bold text-gray-400 px-1 mb-2">
          <span>{selected_month_label}: матчи дня</span>
          <span>{days.length} ставок</span>
        </div>

        {/* Скроллируемый вертикальный столбик матчей */}
        <div 
          ref={daysListRef}
          className="space-y-2 max-h-[380px] xl:max-h-[440px] overflow-y-auto custom-scrollbar pr-1"
        >
          {days.map((item) => {
            // Для сегодняшнего дня синхронизируем с активной ставкой дня на экране!
            let matchName = item.match_name;
            let outcome = item.outcome;
            let odds = item.odds;
            let sportIcon = item.sport_icon;
            let score = item.score;
            let isWin = item.result_status === 'win';
            let isLoss = item.result_status === 'loss';
            let isUpcoming = item.result_status === 'upcoming';
            let profit = item.profit;

            if (item.is_today && is_current_month) {
              if (activeMode === 'botd' && todayBotd) {
                const hName = toRussianTeam(todayBotd.home_team || '');
                const aName = toRussianTeam(todayBotd.away_team || '');
                matchName = todayBotd.match_name || `${hName} — ${aName}`;
                outcome = todayBotd.recommended_outcome || outcome;
                odds = todayBotd.average_odds || odds;
                sportIcon = '⚽';
                if (todayBotd.status === 'finished') {
                  isUpcoming = false;
                  isWin = todayBotd.bet_result === 'win';
                  isLoss = todayBotd.bet_result === 'loss';
                  profit = isWin ? (Math.round(((odds || 1.8) - 1.0) * 100) / 100) : -1.0;
                  if (todayBotd.final_score_home !== null && todayBotd.final_score_away !== null) {
                    score = `${todayBotd.final_score_home} : ${todayBotd.final_score_away}`;
                  }
                } else {
                  isUpcoming = true;
                }
              } else if (activeMode === 'robobet' && todayRobobet) {
                const hName = toRussianTeam(todayRobobet.team1 || '');
                const aName = toRussianTeam(todayRobobet.team2 || '');
                matchName = `${hName} — ${aName}`;
                outcome = todayRobobet.recommendation || outcome;
                odds = todayRobobet.rec_odd || odds;
                sportIcon = '🤖';
                if (todayRobobet.is_finished) {
                  isUpcoming = false;
                  isWin = todayRobobet.result_status === 'win';
                  isLoss = todayRobobet.result_status === 'loss';
                  profit = isWin ? (Math.round(((odds || 1.8) - 1.0) * 100) / 100) : -1.0;
                  score = todayRobobet.score || score;
                } else {
                  isUpcoming = true;
                }
              }
            }

            return (
              <div
                key={item.date}
                className={`p-2.5 rounded-xl border transition-all text-xs ${
                  item.is_today
                    ? 'bg-blue-950/30 border-blue-500/40 shadow-sm shadow-blue-500/10'
                    : isWin 
                    ? 'bg-emerald-950/15 border-emerald-500/25 hover:border-emerald-500/40' 
                    : isLoss
                    ? 'bg-rose-950/15 border-rose-500/25 hover:border-rose-500/40'
                    : 'bg-gray-900/60 border-gray-800 hover:border-gray-700'
                }`}
              >
                {/* Верхняя строка дня: Дата + Статус + Кэф */}
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-black text-gray-300 font-heading text-[11px]">
                      {item.date_display}
                    </span>
                    {item.is_today && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-black bg-blue-500/25 text-blue-300 uppercase">
                        Сегодня
                      </span>
                    )}
                  </div>

                  {/* Бейдж исхода дня */}
                  {isUpcoming ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-amber-400 bg-amber-500/15 px-2 py-0.5 rounded-full border border-amber-500/25">
                      <Clock className="w-3 h-3" />
                      <span>В игре</span>
                    </span>
                  ) : isWin ? (
                    <span className="flex items-center gap-1 text-[10px] font-black text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/30">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Прошло</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-black text-rose-400 bg-rose-500/20 px-2 py-0.5 rounded-full border border-rose-500/30">
                      <XCircle className="w-3 h-3" />
                      <span>Не прошло</span>
                    </span>
                  )}
                </div>

                {/* Матч и команды */}
                <div className="font-bold text-white text-[12px] flex items-center gap-1.5 truncate">
                  <span className="text-sm">{sportIcon}</span>
                  <span className="truncate">{matchName}</span>
                </div>

                {/* Нижняя строчка: Исход, Кэф, Счет */}
                <div className="flex items-center justify-between text-[11px] text-gray-400 mt-1 pt-1 border-t border-gray-800/60">
                  <div className="flex items-center gap-1.5">
                    <span className="font-black text-blue-300 bg-blue-500/15 px-1.5 py-0.2 rounded">
                      {outcome}
                    </span>
                    <span className="font-semibold text-gray-300">
                      кэф {odds}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {score && (
                      <span className="font-black text-gray-200 bg-gray-800/80 px-1.5 py-0.2 rounded text-[11px]">
                        {score}
                      </span>
                    )}
                    {!isUpcoming && (
                      <span className={`font-bold text-[10px] ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {profit >= 0 ? `+${profit}` : profit} флэт
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* 5. ПОДСЧЕТ ЗА ВЫБРАННЫЙ МЕСЯЦ (В КОНЦЕ СПИСКА) */}
        <div className="mt-3.5 p-3 rounded-2xl bg-gradient-to-r from-gray-900 via-[#131b2e] to-gray-900 border border-blue-500/30">
          <div className="text-[11px] font-bold text-gray-300 mb-1 flex items-center justify-between">
            <span>Итог за {selected_month_label}:</span>
            <span className="text-cyan-400 font-black">{selected_month_summary.winrate}% винрейт</span>
          </div>
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-gray-400">
              {selected_month_summary.total_bets} ставок ({selected_month_summary.wins} ✅ / {selected_month_summary.losses} ❌)
            </span>
            <span className={`font-black ${selected_month_summary.profit_units >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {selected_month_summary.profit_units >= 0 ? `+${selected_month_summary.profit_units}` : selected_month_summary.profit_units} флэт (ROI {selected_month_summary.roi}%)
            </span>
          </div>
        </div>

        {/* 6. ССЫЛКИ НА ПРЕДЫДУЩИЕ МЕСЯЦЫ (ВНИЗУ) */}
        <div className="mt-3 pt-3 border-t border-gray-800/80">
          <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2 flex items-center justify-between">
            <span>Архив по месяцам:</span>
            <span className="text-gray-400">клик для выбора</span>
          </div>

          <div className="grid grid-cols-2 gap-1.5 max-h-36 overflow-y-auto custom-scrollbar pr-0.5">
            {available_months.map((m) => {
              const isSel = m.value === selected_month;
              return (
                <button
                  key={m.value}
                  onClick={() => setSelectedMonth(m.value)}
                  className={`p-2 rounded-xl text-left border transition-all ${
                    isSel 
                      ? 'bg-blue-600/30 border-blue-500 text-white font-bold'
                      : 'bg-gray-900/70 hover:bg-gray-800/90 border-gray-800 text-gray-300 hover:text-white'
                  }`}
                >
                  <div className="text-[11px] font-black truncate flex items-center justify-between">
                    <span>{m.label.split(' ')[0]}</span>
                    <span className="text-[10px] text-cyan-400">{m.winrate}%</span>
                  </div>
                  <div className="text-[9px] text-gray-400 flex items-center justify-between mt-0.5">
                    <span>{m.total_bets} ставок</span>
                    <span className="text-emerald-400/90">+{m.profit_units}ф</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
