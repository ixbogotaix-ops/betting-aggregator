import React, { useState, useEffect, useMemo } from 'react';
import { getTopBets, getTodayMatches, getAiAnalysis, getRecentResults, getRobobetPredictions } from './api';
import Header from './components/Header';
import TopBetCard from './components/TopBetCard';
import RobobetCard from './components/RobobetCard';
import MatchList from './components/MatchList';
import SourcesSidebar from './components/SourcesSidebar';
import StatsLeaderboard from './components/StatsLeaderboard';
import DailyParlaysWidget from './components/DailyParlaysWidget';
import RobobetView from './components/RobobetView';
import ArchiveView from './components/ArchiveView';
import MonthlyPerformanceWidget from './components/MonthlyPerformanceWidget';
import { 
  Flame, CalendarDays, AlertTriangle, Bot, CheckCircle2, 
  Trophy, Clock, Zap, ArrowRight, Sparkles, Filter, 
  ArrowUpDown, Users, TrendingUp, Radio, ChevronRight, Search 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getGenericSport, getLocalDateString, toRussianTeam, toRussianMatchName, toRussianLeague } from './utils/russianNames';

const sportsList = [
  { id: 'All', label: 'Все виды', icon: '🏆' },
  { id: 'Football', label: 'Футбол', icon: '⚽' },
  { id: 'Hockey', label: 'Хоккей', icon: '🏒' },
  { id: 'Basketball', label: 'Баскетбол', icon: '🏀' },
  { id: 'MMA', label: 'ММА / Бои', icon: '🥊' },
  { id: 'American Football', label: 'Амер. футбол', icon: '🏈' },
  { id: 'Tennis', label: 'Теннис', icon: '🎾' },
  { id: 'Esports', label: 'Киберспорт', icon: '🎮' },
];

function App() {
  const [currentSport, setCurrentSport] = useState('All');
  const [activeTab, setActiveTab] = useState('botd'); // 'botd', 'cappers', 'parlays', 'matches', 'archive', 'stats'
  const [cappersSort, setCappersSort] = useState('confidence'); // 'confidence', 'odds', 'cappers'
  const [cappersSearch, setCappersSearch] = useState('');
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  
  // Устанавливаем сегодняшнюю локальную дату по умолчанию (формат YYYY-MM-DD без сдвига в UTC)
  const today = getLocalDateString(new Date());
  const [currentDate, setCurrentDate] = useState(today);

  const [allTopBets, setAllTopBets] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [aiVerdict, setAiVerdict] = useState(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [robobetBotd, setRobobetBotd] = useState(null);

  // Загрузка главных ставок дня и фоновая подгрузка расписания
  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setAiVerdict(null);
      try {
        // 1. Моментальная приоритетная загрузка Ставки Дня и Топ-3 прогнозов (300 мс)
        const betsData = await getTopBets('All', currentDate, 'all');
        if (isMounted && Array.isArray(betsData)) {
          setAllTopBets(betsData);
        }
      } catch (err) {
        console.error("Failed to load top bets:", err);
        if (isMounted && (!allTopBets || allTopBets.length === 0)) {
          setError("Сервер обновляет аналитику капперов. Пожалуйста, подождите несколько секунд...");
        }
      } finally {
        if (isMounted) {
          setLoading(false); // Мгновенный показ карточек пользователю!
        }
      }

      // 2. Фоновая неблокирующая подгрузка расписания и робобета
      try {
        const [matchesRes, rRes] = await Promise.allSettled([
          getTodayMatches(currentSport, currentDate),
          getRobobetPredictions()
        ]);

        if (isMounted && matchesRes.status === 'fulfilled' && Array.isArray(matchesRes.value)) {
          setMatches(matchesRes.value);
        }

        if (isMounted && rRes.status === 'fulfilled' && rRes.value?.bet_of_the_day) {
          setRobobetBotd(rRes.value.bet_of_the_day);
        }
      } catch (err) {
        console.error("Background data fetch error:", err);
      }
    };

    fetchData();
    return () => { isMounted = false; };
  }, [currentDate]);

  // При смене спорта обновляем список расписания
  useEffect(() => {
    const updateMatches = async () => {
      try {
        const matchesData = await getTodayMatches(currentSport, currentDate);
        setMatches(matchesData);
      } catch (e) {}
    };
    updateMatches();
  }, [currentSport, currentDate]);

  const handleAiAnalysis = async () => {
    setIsAiLoading(true);
    try {
      const data = await getAiAnalysis(currentSport, currentDate);
      setAiVerdict(data.ai_verdict);
    } catch (err) {
      setAiVerdict("Ошибка при обращении к ИИ.");
    } finally {
      setIsAiLoading(false);
    }
  };

  // Подсчёт количества прогнозов по каждому виду спорта (всегда по полной базе allTopBets!)
  const sportCounts = useMemo(() => {
    const counts = { All: allTopBets.length };
    for (const bet of allTopBets) {
      const gen = getGenericSport(bet.sport_type);
      counts[gen] = (counts[gen] || 0) + 1;
    }
    return counts;
  }, [allTopBets]);

  // Фильтрация прогнозов по выбранному виду спорта (мгновенно, 0 мс задержки)
  const topBets = useMemo(() => {
    if (currentSport === 'All') return allTopBets;
    return allTopBets.filter(b => getGenericSport(b.sport_type) === currentSport);
  }, [allTopBets, currentSport]);

  // 1. Топ-3 Ставки Дня (Ранг 1 - Ставка Дня, Ранг 2 - Топ-2 Дня, Ранг 3 - Топ-3 Дня)
  const top3Bets = useMemo(() => {
    return topBets.slice(0, 3);
  }, [topBets]);

  // Главная Ставка Дня — СТРОГО 1 матч из топ-3 (Ранг 1 с флагом is_bet_of_the_day)
  const mainBotd = useMemo(() => {
    return top3Bets.find(b => b.is_bet_of_the_day) || top3Bets[0] || null;
  }, [top3Bets]);

  // 2. Другие сильные прогнозы и кандидаты дня (начиная с 4-го матча)
  const candidateBets = useMemo(() => {
    return topBets.slice(3);
  }, [topBets]);

  // Сортировка и поиск для раздела "Все прогнозы капперов"
  const sortedCappersBets = useMemo(() => {
    let list = [...topBets];
    if (cappersSearch.trim()) {
      const q = cappersSearch.toLowerCase().trim();
      list = list.filter(b => {
        const homeRu = toRussianTeam(b.home_team || '').toLowerCase();
        const awayRu = toRussianTeam(b.away_team || '').toLowerCase();
        const mRu = toRussianMatchName(b.match_name || '').toLowerCase();
        const lRu = toRussianLeague(b.league || '').toLowerCase();
        const homeOrig = (b.home_team || '').toLowerCase();
        const awayOrig = (b.away_team || '').toLowerCase();
        const mOrig = (b.match_name || '').toLowerCase();
        const lOrig = (b.league || '').toLowerCase();
        return homeRu.includes(q) || awayRu.includes(q) || mRu.includes(q) || lRu.includes(q) ||
               homeOrig.includes(q) || awayOrig.includes(q) || mOrig.includes(q) || lOrig.includes(q);
      });
    }
    if (cappersSort === 'confidence') {
      return list.sort((a, b) => (b.confidence_score || 0) - (a.confidence_score || 0));
    }
    if (cappersSort === 'odds') {
      return list.sort((a, b) => (b.average_odds || 0) - (a.average_odds || 0));
    }
    if (cappersSort === 'cappers') {
      return list.sort((a, b) => {
        const countA = a.all_predictions?.length || a.supporting_sources?.length || 0;
        const countB = b.all_predictions?.length || b.supporting_sources?.length || 0;
        return countB - countA;
      });
    }
    return list;
  }, [topBets, cappersSort, cappersSearch]);



  const activeSportLabel = sportsList.find(s => s.id === currentSport)?.label || currentSport;

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#090d16] text-gray-100 selection:bg-blue-500/30 selection:text-white">
      {/* Новая ультрасовременная двухъярусная шапка с интегрированной навигацией */}
      <Header 
        onOpenSources={() => setIsSourcesOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        botdCount={top3Bets.length}
        cappersCount={topBets.length}
      />

      <div className="flex-grow max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <main className="w-full min-w-0">
          {error && (
            <div className="mb-6 p-4 bg-danger/10 border border-danger/30 rounded-2xl flex items-center gap-3 text-danger shadow-md">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <p className="text-sm font-semibold">{error}</p>
            </div>
          )}

          {/* КОМПАКТНЫЙ СТИЛЬНЫЙ ФИЛЬТР ВИДОВ СПОРТА */}
          {['botd', 'cappers', 'matches', 'archive'].includes(activeTab) && (
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6 p-2 sm:p-2.5 bg-gray-900/40 border border-white/[0.06] rounded-2xl">
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                <span className="text-xs font-black uppercase tracking-wider text-gray-400 px-2 flex items-center gap-1.5">
                  <Filter className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Спорт:</span>
                </span>

                {sportsList.map((sport) => {
                  const isActive = currentSport === sport.id;
                  const count = sport.id === 'All' ? topBets.length : (sportCounts[sport.id] || 0);

                  return (
                    <button
                      key={sport.id}
                      onClick={() => setCurrentSport(sport.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer select-none
                        ${isActive 
                          ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25 ring-1 ring-blue-400 scale-[1.02]' 
                          : 'bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] text-gray-300 hover:text-white'
                        }`}
                    >
                      <span className="text-sm">{sport.icon}</span>
                      <span>{sport.label}</span>
                      {count > 0 && (
                        <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-black ${
                          isActive ? 'bg-white/20 text-white' : 'bg-gray-800 text-gray-300'
                        }`}>
                          {count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              {currentSport !== 'All' && (
                <button
                  onClick={() => setCurrentSport('All')}
                  className="text-xs font-bold text-cyan-400 hover:text-cyan-300 transition-colors px-2 py-1"
                >
                  Сбросить фильтр ✕
                </button>
              )}
            </div>
          )}

          {/* РАЗДЕЛ 1: СТАВКИ ДНЯ И КАНДИДАТЫ (Главный экран) */}
          {activeTab === 'botd' && (
            <div className="flex flex-col lg:flex-row items-start gap-6 lg:gap-8 animate-fade-in">
              {/* ЛЕВАЯ КОЛОНКА В СТОЛБИК: ТРЕКЕР СТАВКИ ДНЯ ПО ДНЯМ И МЕСЯЦАМ */}
              <aside className="w-full lg:w-[350px] xl:w-[380px] shrink-0 lg:sticky lg:top-24">
                <MonthlyPerformanceWidget 
                  todayBotd={mainBotd} 
                  todayRobobet={robobetBotd} 
                />
              </aside>

              {/* ПРАВАЯ ЧАСТЬ: СТАВКИ ДНЯ СЕГОДНЯ, ЭКСПРЕССЫ И КАНДИДАТЫ */}
              <div className="flex-1 min-w-0 space-y-8 w-full">
                {/* Баннер Экспресса Дня */}
                <div 
                  onClick={() => setActiveTab('parlays')}
                className="p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 via-orange-950/30 to-purple-950/30 border border-orange-500/30 hover:border-orange-500/60 transition-all cursor-pointer flex items-center justify-between gap-4 group shadow-lg"
              >
                <div className="flex items-center gap-3.5">
                  <div className="p-2.5 bg-orange-500/20 text-orange-400 rounded-xl group-hover:scale-110 transition-transform">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-sm sm:text-base">Сформирован Экспресс Дня от ИИ</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-orange-500/20 text-orange-300 border border-orange-500/30 animate-pulse">
                        HOT
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Готовые купоны: 🛡️ Надёжный и 🚀 Огненный с калькулятором выигрыша
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-orange-400 font-bold text-xs sm:text-sm group-hover:translate-x-1 transition-transform shrink-0">
                  <span>Открыть купон</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>

              {/* БЛОК 1: ТОП-3 СТАВКИ ДНЯ (Строго 1 ставка дня!) */}
              <section>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2.5">
                      <Sparkles className="w-6 h-6 text-amber-400 animate-pulse" />
                      <span>Топ-3 Ставки Дня {currentSport !== 'All' ? `• ${activeSportLabel}` : ''}</span>
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                      Три лучших зафиксированных матча за день: 👑 <strong>Ставка Дня</strong> (главный фаворит консенсуса) + Топ-2 и Топ-3
                    </p>
                  </div>

                  {topBets.length > 0 && (
                    <button 
                      onClick={handleAiAnalysis}
                      disabled={isAiLoading}
                      className="group relative flex items-center gap-2 bg-gradient-to-r from-blue-600 via-accent to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-5 py-2.5 rounded-xl font-black text-xs sm:text-sm transition-all disabled:opacity-50 overflow-hidden shadow-lg shadow-blue-500/25 shrink-0"
                    >
                      <div className="absolute inset-0 w-full h-full bg-white/20 group-hover:scale-x-100 scale-x-0 origin-left transition-transform duration-300"></div>
                      <Bot className={`w-5 h-5 relative z-10 ${isAiLoading ? 'animate-bounce' : ''}`} />
                      <span className="relative z-10">{isAiLoading ? 'Нейросеть думает...' : 'Получить Супер-Анализ 🚀'}</span>
                    </button>
                  )}
                </div>

                {/* Инсайт нейросети */}
                {aiVerdict && (
                  <div className="mb-8 p-6 bg-gradient-to-br from-card to-gray-900 border border-blue-500/30 rounded-2xl shadow-lg shadow-blue-500/10">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 bg-blue-500/20 rounded-lg">
                        <Bot className="w-6 h-6 text-blue-400" />
                      </div>
                      <h3 className="text-xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-accent">
                        Аналитика Нейросети
                      </h3>
                    </div>
                    <div className="prose prose-invert prose-lg max-w-none text-gray-300 leading-relaxed">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table className="w-full text-left border-collapse" {...props} /></div>,
                          thead: ({node, ...props}) => <thead className="bg-gray-800/50 border-b border-blue-500/30" {...props} />,
                          th: ({node, ...props}) => <th className="p-3 text-blue-400 font-bold" {...props} />,
                          td: ({node, ...props}) => <td className="p-3 border-b border-gray-800/50" {...props} />,
                          strong: ({node, ...props}) => <strong className="text-white font-black" {...props} />,
                          h1: ({node, ...props}) => <h1 className="text-2xl font-bold text-white mb-4 mt-6" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-xl font-bold text-white mb-3 mt-5" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-lg font-bold text-white mb-2 mt-4" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-2" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-2" {...props} />,
                          li: ({node, ...props}) => <li className="text-gray-300" {...props} />
                        }}
                      >
                        {aiVerdict}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Сетка Топ-3 Ставок Дня (Только 1 из трех является Ставкой Дня!) */}
                {loading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-64 bg-card rounded-2xl border border-gray-800 animate-pulse"></div>
                    ))}
                  </div>
                ) : top3Bets.length > 0 ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
                      {top3Bets.map(bet => (
                        <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
                      ))}
                    </div>

                    {/* Дополнительная карточка от Робобет ИИ */}
                    {(currentSport === 'All' || currentSport === 'Football') && robobetBotd && (
                      <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-950/20 via-cyan-950/20 to-gray-900 border border-cyan-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <Bot className="w-4 h-4 text-cyan-400" />
                          <span className="text-xs font-black text-cyan-300 uppercase tracking-wider font-heading">
                            Математический выбор дня • Робобет ИИ
                          </span>
                        </div>
                        <div className="max-w-md">
                          <RobobetCard 
                            botd={robobetBotd} 
                            onOpenRobobetTab={() => setActiveTab('robobet')} 
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-gray-900/50 rounded-3xl border border-gray-800 text-gray-400">
                    <Sparkles className="w-10 h-10 text-amber-500/40 mx-auto mb-2" />
                    <p className="text-base font-bold text-gray-200">Ставки дня для этой категории формируются</p>
                  </div>
                )}
              </section>

              {/* БЛОК 2: ДРУГИЕ СТАВКИ (КАНДИДАТЫ, ИЗ КОТОРЫХ ВЫБИРАЛАСЬ СТАВКА ДНЯ) */}
              {candidateBets.length > 0 && (
                <section className="pt-8 border-t border-gray-800/80">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
                    <div>
                      <h3 className="text-lg sm:text-xl font-black text-gray-100 flex items-center gap-2">
                        <Flame className="w-5 h-5 text-orange-400" />
                        <span>Другие уверенные прогнозы капперов {currentSport !== 'All' ? `• ${activeSportLabel}` : ''}</span>
                        <span className="text-xs font-bold px-2.5 py-0.5 bg-blue-500/15 text-blue-400 rounded-full border border-blue-500/25">
                          {candidateBets.length} матчей
                        </span>
                      </h3>
                      <p className="text-xs text-gray-400 mt-1">
                        Ординарные прогнозы с высоким консенсусом экспертов, из которых отбиралась главная Ставка Дня
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
                    {candidateBets.map(bet => (
                      <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
                    ))}
                  </div>
                </section>
              )}
              </div>
            </div>
          )}

          {/* РАЗДЕЛ: РОБОБЕТ ИИ (МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ВЕРОЯТНОСТЕЙ) */}
          {activeTab === 'robobet' && (
            <RobobetView topBets={topBets} />
          )}

          {/* РАЗДЕЛ 2: ВСЕ ПРОГНОЗЫ КАППЕРОВ (Сортировка и каталог) */}
          {activeTab === 'cappers' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 sm:p-5 bg-gray-900/60 rounded-2xl border border-gray-800">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
                    <Flame className="w-6 h-6 text-orange-400" />
                    <span>Все прогнозы топ-капперов {currentSport !== 'All' ? `• ${activeSportLabel}` : ''}</span>
                    <span className="text-sm font-semibold px-2.5 py-0.5 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20">
                      {sortedCappersBets.length} прогнозов
                    </span>
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Полный каталог всех исходов от капперов Рунета с возможностью сортировки
                  </p>
                </div>

                {/* Поиск и панель сортировки */}
                <div className="flex flex-wrap items-center gap-3">
                  {/* Быстрый поиск прогноза */}
                  <div className="relative min-w-[200px] max-w-xs flex-1">
                    <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                      type="text"
                      value={cappersSearch}
                      onChange={(e) => setCappersSearch(e.target.value)}
                      placeholder="Поиск по команде/лиге..."
                      className="w-full bg-gray-950/90 border border-gray-800 rounded-xl pl-8 pr-7 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                    />
                    {cappersSearch && (
                      <button
                        onClick={() => setCappersSearch('')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white text-xs"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  {/* Панель сортировки */}
                  <div className="flex items-center gap-1.5 p-1 bg-gray-950/80 rounded-xl border border-gray-800 shrink-0">
                    <span className="text-[11px] font-bold text-gray-500 px-2 flex items-center gap-1">
                      <ArrowUpDown className="w-3 h-3" />
                      <span>Сортировка:</span>
                    </span>
                    <button
                      onClick={() => setCappersSort('confidence')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        cappersSort === 'confidence'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      ⚡ По уверенности
                    </button>
                    <button
                      onClick={() => setCappersSort('odds')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        cappersSort === 'odds'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      📈 По коэффициенту
                    </button>
                    <button
                      onClick={() => setCappersSort('cappers')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        cappersSort === 'cappers'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      👥 По числу капперов
                    </button>
                  </div>
                </div>
              </div>

              {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="h-64 bg-card rounded-2xl border border-gray-800 animate-pulse"></div>
                  ))}
                </div>
              ) : sortedCappersBets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
                  {sortedCappersBets.map(bet => (
                    <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-card rounded-2xl border border-gray-800 text-gray-500">
                  {error ? "Ошибка загрузки данных" : "На сегодня нет уверенных прогнозов для этой категории."}
                </div>
              )}
            </div>
          )}

          {/* РАЗДЕЛ 3: ЭКСПРЕСС ДНЯ */}
          {activeTab === 'parlays' && (
            <div className="animate-fade-in">
              <DailyParlaysWidget />
            </div>
          )}

          {/* РАЗДЕЛ 4: ВСЕ МАТЧИ И ЛИНИЯ РАСПИСАНИЯ */}
          {activeTab === 'matches' && (
            <section className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
                    <CalendarDays className="w-6 h-6 text-cyan-400" />
                    <span>Расписание матчей и Линия {currentSport !== 'All' ? `• ${activeSportLabel}` : ''}</span>
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Все события на выбранную дату с распределением мнений капперов
                  </p>
                </div>
                
                <input 
                  type="date" 
                  value={currentDate}
                  onChange={(e) => setCurrentDate(e.target.value)}
                  className="bg-card text-white border border-gray-700 rounded-xl px-4 py-2 outline-none focus:border-accent text-sm font-semibold shadow-inner"
                />
              </div>
              
              <div className="bg-card rounded-2xl border border-gray-800 overflow-hidden shadow-sm">
                {loading ? (
                  <div className="p-12 text-center text-gray-500 animate-pulse">Загрузка расписания матчей...</div>
                ) : (
                  <MatchList matches={matches} />
                )}
              </div>
            </section>
          )}

          {/* РАЗДЕЛ 5: ИНТЕРАКТИВНЫЙ АРХИВ ЗАВЕРШЁННЫХ МАТЧЕЙ И TRACK RECORD */}
          {activeTab === 'archive' && (
            <ArchiveView 
              currentSport={currentSport} 
              activeSportLabel={activeSportLabel} 
            />
          )}

          {/* РАЗДЕЛ 6: РЕЙТИНГ КАППЕРОВ И СТАТИСТИКА */}
          {activeTab === 'stats' && (
            <div className="animate-fade-in">
              <StatsLeaderboard />
            </div>
          )}

        </main>
      </div>

      {/* Выдвижная панель мониторинга источников (Drawer) */}
      <SourcesSidebar 
        isOpen={isSourcesOpen} 
        onClose={() => setIsSourcesOpen(false)} 
      />

      {/* Плавающая кнопка для быстрого открытия мониторинга источников */}
      <button
        onClick={() => setIsSourcesOpen(true)}
        title="Мониторинг источников и капперов"
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-gray-900/90 hover:bg-gray-850 border border-gray-700/80 text-gray-200 shadow-2xl backdrop-blur-md transition-all hover:scale-105 active:scale-95 group ring-1 ring-blue-500/30 cursor-pointer"
      >
        <div className="relative flex items-center justify-center">
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-gray-900"></span>
        </div>
        <span className="text-xs font-black tracking-wide hidden sm:inline">Источники</span>
      </button>

      <footer className="border-t border-gray-800 mt-auto bg-dark">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
          &copy; {new Date().getFullYear()} AI Sports Aggregator. Данные носят рекомендательный характер.
        </div>
      </footer>
    </div>
  );
}

export default App;
