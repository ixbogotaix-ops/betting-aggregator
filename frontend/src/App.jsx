import React, { useState, useEffect, useMemo } from 'react';
import { getTopBets, getTodayMatches, getAiAnalysis, getRecentResults } from './api';
import Header from './components/Header';
import TopBetCard from './components/TopBetCard';
import MatchList from './components/MatchList';
import SourcesSidebar from './components/SourcesSidebar';
import StatsLeaderboard from './components/StatsLeaderboard';
import DailyParlaysWidget from './components/DailyParlaysWidget';
import { 
  Flame, CalendarDays, AlertTriangle, Bot, CheckCircle2, 
  Trophy, Clock, Zap, ArrowRight, Sparkles, Filter, 
  ArrowUpDown, Users, TrendingUp, Radio 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [currentSport, setCurrentSport] = useState('All');
  const [activeTab, setActiveTab] = useState('botd'); // 'botd', 'cappers', 'parlays', 'matches', 'archive', 'stats'
  const [cappersSort, setCappersSort] = useState('confidence'); // 'confidence', 'odds', 'cappers'
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  
  // Устанавливаем сегодняшнюю дату по умолчанию (формат YYYY-MM-DD)
  const today = new Date().toISOString().split('T')[0];
  const [currentDate, setCurrentDate] = useState(today);

  const [topBets, setTopBets] = useState([]);
  const [matches, setMatches] = useState([]);
  const [archiveBets, setArchiveBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingArchive, setLoadingArchive] = useState(false);
  const [error, setError] = useState(null);
  
  const [aiVerdict, setAiVerdict] = useState(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Загрузка предстоящих матчей
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setAiVerdict(null);
      try {
        const [betsData, matchesData] = await Promise.all([
          getTopBets(currentSport, currentDate, 'upcoming'),
          getTodayMatches(currentSport, currentDate)
        ]);
        setTopBets(betsData);
        setMatches(matchesData);
      } catch (err) {
        setError("Не удалось загрузить данные. Убедитесь, что бэкенд запущен на порту 8000.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentSport, currentDate]);

  // Загрузка архива при переключении на вкладку 'archive'
  useEffect(() => {
    if (activeTab === 'archive') {
      const fetchArchive = async () => {
        setLoadingArchive(true);
        try {
          const data = await getRecentResults(currentSport);
          setArchiveBets(data);
        } catch (err) {
          console.error(err);
        } finally {
          setLoadingArchive(false);
        }
      };
      fetchArchive();
    }
  }, [activeTab, currentSport]);

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

  // Ставки дня: ровно по 1 лучшей ставке на каждый вид спорта (флаг is_bet_of_the_day)
  const botdBets = useMemo(() => {
    const bets = topBets.filter(b => b.is_bet_of_the_day);
    if (bets.length > 0) return bets;
    const seen = new Set();
    const res = [];
    for (const b of topBets) {
      const s = (b.sport_type || '').toLowerCase();
      if (!seen.has(s)) {
        seen.add(s);
        res.push({ ...b, is_bet_of_the_day: true });
      }
    }
    return res;
  }, [topBets]);

  // Сортировка для раздела "Лучшие от капперов"
  const sortedCappersBets = useMemo(() => {
    const list = [...topBets];
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
  }, [topBets, cappersSort]);

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <Header 
        currentSport={currentSport} 
        onSportChange={setCurrentSport} 
        onOpenSources={() => setIsSourcesOpen(true)}
      />

      <div className="flex-grow max-w-[1400px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <main className="w-full min-w-0">
          {error && (
            <div className="mb-8 p-4 bg-danger/10 border border-danger/30 rounded-lg flex items-center gap-3 text-danger">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {/* НАВИГАЦИЯ ПО РАЗДЕЛАМ (КНОПКИ ТАБОВ) */}
          <div className="flex items-center gap-2 p-1.5 bg-gray-900/90 border border-gray-800 rounded-2xl mb-8 overflow-x-auto shadow-md scrollbar-none [&::-webkit-scrollbar]:hidden">
            <button
              onClick={() => setActiveTab('botd')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black transition-all whitespace-nowrap ${
                activeTab === 'botd'
                  ? 'bg-gradient-to-r from-amber-500 via-amber-600 to-orange-600 text-white shadow-lg shadow-amber-500/25 ring-1 ring-amber-400/50 scale-[1.02]'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>🏆 Ставки Дня</span>
              {botdBets.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-black bg-white/20 text-white">
                  {botdBets.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('cappers')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black transition-all whitespace-nowrap ${
                activeTab === 'cappers'
                  ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-blue-500/25 ring-1 ring-blue-400/50 scale-[1.02]'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Flame className="w-4 h-4 text-orange-400" />
              <span>🔥 Лучшие от Капперов</span>
              {topBets.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-black bg-white/20 text-white">
                  {topBets.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('parlays')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black transition-all whitespace-nowrap ${
                activeTab === 'parlays'
                  ? 'bg-gradient-to-r from-orange-500 to-red-600 text-white shadow-lg shadow-orange-500/25 ring-1 ring-orange-400/50 scale-[1.02]'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Zap className="w-4 h-4 text-amber-300" />
              <span>⚡ Экспресс Дня</span>
            </button>

            <button
              onClick={() => setActiveTab('matches')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black transition-all whitespace-nowrap ${
                activeTab === 'matches'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/25 ring-1 ring-cyan-400/50 scale-[1.02]'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <CalendarDays className="w-4 h-4 text-cyan-300" />
              <span>📋 Расписание матчей</span>
            </button>

            <button
              onClick={() => setActiveTab('archive')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black transition-all whitespace-nowrap ${
                activeTab === 'archive'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/25 ring-1 ring-emerald-400/50 scale-[1.02]'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Архив счетов</span>
            </button>

            <button
              onClick={() => setActiveTab('stats')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black transition-all whitespace-nowrap ${
                activeTab === 'stats'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/25 ring-1 ring-purple-400/50 scale-[1.02]'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Trophy className="w-4 h-4 text-yellow-400" />
              <span>Рейтинг капперов</span>
            </button>
          </div>

          {/* РАЗДЕЛ 1: СТАВКИ ДНЯ ПО ВИДАМ СПОРТА (Главный экран) */}
          {activeTab === 'botd' && (
            <div className="space-y-8 animate-fade-in">
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

              {/* Заголовок секции Ставок Дня */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
                    <Sparkles className="w-6 h-6 text-amber-400 animate-pulse" />
                    <span>Главные Ставки Дня по видам спорта</span>
                  </h2>
                  <p className="text-xs sm:text-sm text-gray-400 mt-1">
                    По 1 самому надежному и выверенному матчу на каждый вид спорта от нейросети и топ-экспертов
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
                <div className="p-6 bg-gradient-to-br from-card to-gray-900 border border-blue-500/30 rounded-2xl shadow-lg shadow-blue-500/10">
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

              {/* Сетка Ставок Дня */}
              {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-64 bg-card rounded-2xl border border-gray-800 animate-pulse"></div>
                  ))}
                </div>
              ) : botdBets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
                  {botdBets.map(bet => (
                    <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-gray-900/50 rounded-3xl border border-gray-800 text-gray-400">
                  <Sparkles className="w-12 h-12 text-amber-500/40 mx-auto mb-3" />
                  <p className="text-base font-bold text-gray-200">Ставки дня формируются</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Капперы и нейросеть анализируют предстоящие матчи для этой категории.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* РАЗДЕЛ 2: ЛУЧШИЕ ОТ КАППЕРОВ (Все топовые прогнозы с консенсусом) */}
          {activeTab === 'cappers' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-gray-900/60 rounded-2xl border border-gray-800">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
                    <Flame className="w-6 h-6 text-orange-400" />
                    <span>Лучшие ставки от капперов</span>
                    <span className="text-sm font-semibold px-2.5 py-0.5 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20">
                      {sortedCappersBets.length} прогнозов
                    </span>
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Полный список матчей с максимальным консенсусом ведущих аналитиков Рунета
                  </p>
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
                    <span>Расписание матчей и Линия</span>
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

          {/* РАЗДЕЛ 5: АРХИВ ЗАВЕРШЁННЫХ МАТЧЕЙ И СЧЕТА */}
          {activeTab === 'archive' && (
            <section className="space-y-6 animate-fade-in">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                    <span>Архив завершённых матчей</span>
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Финальные счета и автоматическая верификация проходимости ставок
                  </p>
                </div>
              </div>

              {loadingArchive ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-64 bg-card rounded-2xl border border-gray-800 animate-pulse"></div>
                  ))}
                </div>
              ) : archiveBets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
                  {archiveBets.map(bet => (
                    <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-gray-900/60 rounded-3xl border border-gray-800 text-gray-400">
                  <CheckCircle2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-base font-semibold text-gray-300">Завершённых событий пока нет</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Как только сегодняшние матчи закончатся, их финальный счёт и результат отобразятся здесь.
                  </p>
                </div>
              )}
            </section>
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
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-gray-900/90 hover:bg-gray-800 border border-gray-700/80 text-gray-200 shadow-2xl backdrop-blur-md transition-all hover:scale-105 active:scale-95 group ring-1 ring-blue-500/30"
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
