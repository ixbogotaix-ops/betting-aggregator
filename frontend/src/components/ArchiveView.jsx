import React, { useState, useEffect, useMemo } from 'react';
import { 
  CheckCircle2, XCircle, RotateCcw, Calendar, TrendingUp, 
  Target, Sparkles, Filter, RefreshCw, Trophy, Shield, 
  ChevronLeft, ChevronRight, BarChart3, Bot, Users, Award
} from 'lucide-react';
import TopBetCard from './TopBetCard';
import { getRecentResults, getArchiveSummary, syncMatchResults } from '../api';
import { getLocalDateString } from '../utils/russianNames';

const RU_DAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const RU_MONTHS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

const formatDayLabel = (dateStr) => {
  if (!dateStr || dateStr === 'ALL') return 'За всё время';
  try {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const d = new Date(year, month, day);
      const dayOfWeek = RU_DAYS[d.getDay()];
      const monthName = RU_MONTHS[month];
      return `${dayOfWeek}, ${day} ${monthName}`;
    }
  } catch (e) {}
  return dateStr;
};

const ArchiveView = ({ currentSport = 'All', activeSportLabel = 'Все виды' }) => {
  const [selectedDate, setSelectedDate] = useState('ALL');
  const [outcomeFilter, setOutcomeFilter] = useState('all'); // 'all', 'win', 'loss', 'refund'
  const [categoryFilter, setCategoryFilter] = useState('all'); // 'all', 'botd', 'cappers', 'robobet'
  
  const [bets, setBets] = useState([]);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);

  // Генерируем список последних 10 дней для быстрого выбора (по локальному времени)
  const recentDays = useMemo(() => {
    const days = [];
    const now = new Date();
    for (let i = 0; i < 10; i++) {
      const d = new Date(now.getTime() - i * 86400000);
      const iso = getLocalDateString(d);
      const dayOfWeek = RU_DAYS[d.getDay()];
      const dayNum = d.getDate();
      const monthName = RU_MONTHS[d.getMonth()];
      
      let label = `${dayNum} ${monthName}`;
      if (i === 0) label = 'Сегодня';
      else if (i === 1) label = 'Вчера';
      else if (i === 2) label = 'Позавчера';

      days.push({
        iso,
        dayOfWeek,
        label,
        dayNum,
        monthName
      });
    }
    return days;
  }, []);

  // Загрузка календарной сводки по дням
  const loadSummary = async () => {
    try {
      const summary = await getArchiveSummary(currentSport);
      if (summary) {
        setSummaryData(summary);
      }
    } catch (e) {
      console.error("Ошибка загрузки сводки архива:", e);
    }
  };

  // Загрузка матчей для выбранной даты и фильтров
  const loadMatches = async () => {
    setLoading(true);
    try {
      const data = await getRecentResults(
        currentSport,
        selectedDate,
        categoryFilter,
        outcomeFilter
      );
      setBets(data || []);
    } catch (e) {
      console.error("Ошибка загрузки результатов архива:", e);
      setBets([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [currentSport]);

  useEffect(() => {
    loadMatches();
  }, [selectedDate, currentSport, categoryFilter, outcomeFilter]);

  // Ручная синхронизация счетов
  const handleSyncResults = async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    setSyncStatus('Синхронизация результатов с ESPN, Zulubet и Robobet...');
    try {
      await syncMatchResults();
      setTimeout(async () => {
        await Promise.all([loadSummary(), loadMatches()]);
        setSyncStatus('Результаты успешно обновлены!');
        setTimeout(() => setSyncStatus(null), 3500);
        setIsSyncing(false);
      }, 2500);
    } catch (e) {
      setSyncStatus('Ошибка запуска синхронизации.');
      setTimeout(() => setSyncStatus(null), 3000);
      setIsSyncing(false);
    }
  };

  // Словарь сводок по дням из бэкенда для быстрых бейджей на календаре
  const daySummaryMap = useMemo(() => {
    const map = {};
    if (summaryData?.days) {
      for (const d of summaryData.days) {
        map[d.date] = d;
      }
    }
    return map;
  }, [summaryData]);

  // Статистика для отображения в Hero-блоке
  const currentStats = useMemo(() => {
    const isFiltered = categoryFilter !== 'all' || outcomeFilter !== 'all';

    // Если нет фильтров по категориям и исходам, берем агрегированную сводку бэкенда
    if (!isFiltered) {
      // Если выбрано конкретное число и в сводке есть данные
      if (selectedDate !== 'ALL' && daySummaryMap[selectedDate]) {
        const s = daySummaryMap[selectedDate];
        return {
          total: s.total_matches,
          wins: s.wins,
          losses: s.losses,
          refunds: s.refunds,
          winrate: s.winrate,
          profitUnits: s.profit_units,
          roi: s.roi
        };
      }

      // Если "За всё время", берем overall из бэкенда
      if (selectedDate === 'ALL' && summaryData?.overall && summaryData.overall.total_matches > 0) {
        const o = summaryData.overall;
        return {
          total: o.total_matches,
          wins: o.wins,
          losses: o.losses,
          refunds: o.refunds,
          winrate: o.winrate,
          profitUnits: o.profit_units,
          roi: o.roi
        };
      }
    }

    // Динамический подсчет по загруженным отфильтрованным карточкам
    let wins = 0;
    let losses = 0;
    let refunds = 0;
    let profitUnits = 0.0;

    for (const b of bets) {
      if (b.bet_result === 'win') {
        wins++;
        profitUnits += ((b.average_odds || 1.8) - 1.0);
      } else if (b.bet_result === 'loss') {
        losses++;
        profitUnits -= 1.0;
      } else if (b.bet_result === 'refund') {
        refunds++;
      }
    }
    const decided = wins + losses;
    const winrate = decided > 0 ? Math.round((wins / decided) * 100) : 0;
    const roi = decided > 0 ? Math.round((profitUnits / decided) * 100) : 0;

    return {
      total: bets.length,
      wins,
      losses,
      refunds,
      winrate,
      profitUnits: Number(profitUnits.toFixed(2)),
      roi
    };
  }, [selectedDate, daySummaryMap, summaryData, bets, categoryFilter, outcomeFilter]);

  return (
    <section className="space-y-6 animate-fade-in">
      {/* 1. ГЛАВНАЯ ПАНЕЛЬ ШАПКИ АРХИВА */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 bg-gradient-to-r from-gray-900/90 via-gray-900 to-gray-950 rounded-3xl border border-gray-800 shadow-2xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-inner">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
                <span>Архив ставок & Track Record</span>
                <span className="text-xs font-bold px-2.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
                  {bets.length} завершено
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Прозрачная история: официальные финальные счета (ESPN/Zulubet/Robobet), расчет ROI и проходимости
              </p>
            </div>
          </div>
        </div>

        {/* Кнопка ручной синхронизации результатов */}
        <div className="flex items-center gap-3 shrink-0">
          {syncStatus && (
            <span className="text-xs text-emerald-400 font-semibold animate-pulse">
              {syncStatus}
            </span>
          )}
          <button
            onClick={handleSyncResults}
            disabled={isSyncing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gray-800/90 hover:bg-gray-750 border border-gray-700 text-gray-200 hover:text-white text-xs font-bold transition-all shadow-md active:scale-95 disabled:opacity-50"
            title="Обновить финальные счета и пересчитать профит"
          >
            <RefreshCw className={`w-4 h-4 text-emerald-400 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Проверка счетов...' : 'Сверить результаты'}</span>
          </button>
        </div>
      </div>

      {/* 2. ИНТЕРАКТИВНАЯ КАЛЕНДАРНАЯ ЛЕНТА (DAY-BY-DAY NAVIGATION) */}
      <div className="bg-gray-900/60 p-3 sm:p-4 rounded-3xl border border-gray-800/90 shadow-lg">
        <div className="flex items-center justify-between gap-3 mb-3 px-1">
          <div className="flex items-center gap-2 text-xs font-black text-gray-300 uppercase tracking-wider">
            <Calendar className="w-4 h-4 text-blue-400" />
            <span>Календарь дней</span>
          </div>

          {/* Инпут произвольной даты */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-gray-500 hidden sm:inline">Выбрать любую дату:</span>
            <input 
              type="date" 
              value={selectedDate === 'ALL' ? '' : selectedDate}
              onChange={(e) => setSelectedDate(e.target.value || 'ALL')}
              className="bg-gray-950 text-white border border-gray-700/80 rounded-xl px-3 py-1.5 outline-none focus:border-emerald-500 text-xs font-bold shadow-inner"
            />
          </div>
        </div>

        {/* Горизонтальный скролл плашек дней */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-800">
          {/* Кнопка "За всё время" */}
          <button
            onClick={() => setSelectedDate('ALL')}
            className={`flex flex-col items-center justify-center min-w-[110px] px-3 py-2 rounded-2xl border transition-all shrink-0 ${
              selectedDate === 'ALL'
                ? 'bg-gradient-to-b from-emerald-600 to-emerald-700 text-white border-emerald-400/50 shadow-lg shadow-emerald-500/20 scale-[1.02]'
                : 'bg-gray-950/80 hover:bg-gray-850 text-gray-400 hover:text-gray-200 border-gray-800'
            }`}
          >
            <span className="text-[10px] font-black uppercase tracking-wider opacity-80">Весь период</span>
            <span className="text-sm font-black mt-0.5">Вся история</span>
            {summaryData?.overall && (
              <span className={`text-[10px] font-bold mt-1 px-1.5 py-0.2 rounded ${
                selectedDate === 'ALL' ? 'bg-black/30 text-white' : 'text-emerald-400'
              }`}>
                {summaryData.overall.winrate}% • {summaryData.overall.total_matches} матчей
              </span>
            )}
          </button>

          {/* Плашки прошедших дней */}
          {recentDays.map((day) => {
            const dStat = daySummaryMap[day.iso];
            const isSelected = selectedDate === day.iso;
            const hasData = Boolean(dStat && dStat.total_matches > 0);

            return (
              <button
                key={day.iso}
                onClick={() => setSelectedDate(day.iso)}
                className={`flex flex-col items-center justify-center min-w-[96px] px-2.5 py-2 rounded-2xl border transition-all shrink-0 relative ${
                  isSelected
                    ? 'bg-gradient-to-b from-blue-600 to-indigo-700 text-white border-blue-400/60 shadow-lg shadow-blue-500/25 scale-[1.02]'
                    : 'bg-gray-950/80 hover:bg-gray-850 text-gray-400 hover:text-gray-200 border-gray-800'
                }`}
              >
                <span className={`text-[10px] font-bold uppercase tracking-wider ${
                  isSelected ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {day.dayOfWeek} • {day.label}
                </span>

                <span className="text-xs font-black mt-0.5">
                  {day.dayNum} {day.monthName}
                </span>

                {/* Мини-бейдж доходности за этот день */}
                {hasData ? (
                  <span className={`text-[9px] font-black mt-1 px-1.5 py-0.5 rounded-full ${
                    isSelected 
                      ? 'bg-black/30 text-white' 
                      : dStat.profit_units >= 0 
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}>
                    {dStat.profit_units >= 0 ? `+${dStat.profit_units}u` : `${dStat.profit_units}u`} ({dStat.winrate}%)
                  </span>
                ) : (
                  <span className={`text-[9px] font-semibold mt-1 opacity-50 ${isSelected ? 'text-white' : 'text-gray-600'}`}>
                    нет ставок
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. HERO СВОДКА ПРОХОДИМОСТИ И ROI (KPI CARDS) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Рассчитано */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-4 text-center shadow-md">
          <div className="text-[11px] text-gray-400 font-bold uppercase tracking-wider mb-1">Матчей рассчитано</div>
          <div className="text-2xl font-black text-white">{currentStats.total}</div>
          <div className="text-[10px] text-gray-500 font-semibold mt-0.5">
            {formatDayLabel(selectedDate)}
          </div>
        </div>

        {/* Выиграно */}
        <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-4 text-center shadow-md">
          <div className="text-[11px] text-emerald-400 font-bold uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Выиграно</span>
          </div>
          <div className="text-2xl font-black text-emerald-400">+{currentStats.wins}</div>
          <div className="text-[10px] text-emerald-500/80 font-semibold mt-0.5">успешных пари</div>
        </div>

        {/* Проиграно */}
        <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-4 text-center shadow-md">
          <div className="text-[11px] text-rose-400 font-bold uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
            <XCircle className="w-3.5 h-3.5" />
            <span>Проиграно</span>
          </div>
          <div className="text-2xl font-black text-rose-400">{currentStats.losses}</div>
          <div className="text-[10px] text-rose-500/80 font-semibold mt-0.5">не зашло</div>
        </div>

        {/* Возвраты */}
        <div className="bg-amber-950/20 border border-amber-500/30 rounded-2xl p-4 text-center shadow-md">
          <div className="text-[11px] text-amber-400 font-bold uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Возвраты</span>
          </div>
          <div className="text-2xl font-black text-amber-400">{currentStats.refunds}</div>
          <div className="text-[10px] text-amber-500/80 font-semibold mt-0.5">расчет с кэфом 1.0</div>
        </div>

        {/* Винрейт */}
        <div className="bg-blue-950/20 border border-blue-500/30 rounded-2xl p-4 text-center shadow-md">
          <div className="text-[11px] text-blue-400 font-bold uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
            <Target className="w-3.5 h-3.5" />
            <span>Винрейт</span>
          </div>
          <div className="text-2xl font-black text-blue-400">{currentStats.winrate}%</div>
          <div className="text-[10px] text-blue-400/80 font-semibold mt-0.5">проходимость</div>
        </div>

        {/* Профит и ROI */}
        <div className={`border rounded-2xl p-4 text-center shadow-md ${
          currentStats.profitUnits >= 0 
            ? 'bg-emerald-950/25 border-emerald-500/40' 
            : 'bg-rose-950/25 border-rose-500/40'
        }`}>
          <div className="text-[11px] text-gray-300 font-bold uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Профит (ROI)</span>
          </div>
          <div className={`text-2xl font-black ${
            currentStats.profitUnits >= 0 ? 'text-emerald-400' : 'text-rose-400'
          }`}>
            {currentStats.profitUnits >= 0 ? `+${currentStats.profitUnits}` : currentStats.profitUnits} ф
          </div>
          <div className={`text-[11px] font-black mt-0.5 ${
            currentStats.roi >= 0 ? 'text-emerald-300' : 'text-rose-300'
          }`}>
            ROI: {currentStats.roi >= 0 ? `+${currentStats.roi}%` : `${currentStats.roi}%`}
          </div>
        </div>
      </div>

      {/* 4. ФИЛЬТРЫ ПО КАТЕГОРИИ И РЕЗУЛЬТАТУ ИСХОДА */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-gray-900/50 rounded-2xl border border-gray-800">
        {/* Фильтр по категории источника */}
        <div className="flex items-center gap-1 bg-gray-950 p-1 rounded-xl border border-gray-800">
          <button
            onClick={() => setCategoryFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              categoryFilter === 'all'
                ? 'bg-gray-800 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Все события
          </button>
          <button
            onClick={() => setCategoryFilter('botd')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              categoryFilter === 'botd'
                ? 'bg-amber-600/80 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3 h-3 text-amber-400" />
            <span>Ставки дня</span>
          </button>
          <button
            onClick={() => setCategoryFilter('cappers')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              categoryFilter === 'cappers'
                ? 'bg-blue-600/80 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Users className="w-3 h-3 text-blue-400" />
            <span>Капперы</span>
          </button>
          <button
            onClick={() => setCategoryFilter('robobet')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              categoryFilter === 'robobet'
                ? 'bg-purple-600/80 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Bot className="w-3 h-3 text-purple-400" />
            <span>Робобет ИИ</span>
          </button>
        </div>

        {/* Фильтр по исходу (Выигрыш / Проигрыш / Возврат) */}
        <div className="flex items-center gap-1 bg-gray-950 p-1 rounded-xl border border-gray-800">
          <button
            onClick={() => setOutcomeFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              outcomeFilter === 'all'
                ? 'bg-gray-800 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Все исходы
          </button>
          <button
            onClick={() => setOutcomeFilter('win')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              outcomeFilter === 'win'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-400/80 hover:text-emerald-300'
            }`}
          >
            <span>✅ Выигрыши</span>
          </button>
          <button
            onClick={() => setOutcomeFilter('loss')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              outcomeFilter === 'loss'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-rose-400/80 hover:text-rose-300'
            }`}
          >
            <span>❌ Проигрыши</span>
          </button>
          <button
            onClick={() => setOutcomeFilter('refund')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              outcomeFilter === 'refund'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-amber-400/80 hover:text-amber-300'
            }`}
          >
            <span>🔄 Возвраты</span>
          </button>
        </div>
      </div>

      {/* 5. СЕТКА КАРТОЧЕК ЗАВЕРШЁННЫХ МАТЧЕЙ */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-64 bg-card rounded-3xl border border-gray-800 animate-pulse"></div>
          ))}
        </div>
      ) : bets.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
          {bets.map(bet => (
            <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-gray-900/60 rounded-3xl border border-gray-800 text-gray-400">
          <CheckCircle2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-base font-bold text-gray-200">
            Завершённых событий по выбранным критериям не найдено
          </p>
          <p className="text-xs text-gray-500 mt-1 mb-5 max-w-md mx-auto">
            Попробуйте сбросить фильтр исхода или выберите другую дату в интерактивной ленте календаря.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => {
                setSelectedDate('ALL');
                setOutcomeFilter('all');
                setCategoryFilter('all');
              }}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-md active:scale-95"
            >
              Сбросить фильтры и показать архив за всё время
            </button>
          </div>
        </div>
      )}
    </section>
  );
};

export default ArchiveView;
