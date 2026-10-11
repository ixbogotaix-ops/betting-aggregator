import React, { useState, useEffect } from 'react';
import { getTopBets, getTodayMatches, getAiAnalysis, getRecentResults } from './api';
import Header from './components/Header';
import TopBetCard from './components/TopBetCard';
import MatchList from './components/MatchList';
import SourcesSidebar from './components/SourcesSidebar';
import StatsLeaderboard from './components/StatsLeaderboard';
import { Flame, CalendarDays, AlertTriangle, Bot, CheckCircle2, Trophy, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [currentSport, setCurrentSport] = useState('All');
  const [activeTab, setActiveTab] = useState('upcoming'); // 'upcoming', 'archive', 'stats'
  
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

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <Header currentSport={currentSport} onSportChange={setCurrentSport} />

      <div className="flex-grow max-w-[1400px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        {/* Боковой дебаг-сайдбар */}
        <SourcesSidebar />

        <main className="flex-1 w-full min-w-0">
          {error && (
            <div className="mb-8 p-4 bg-danger/10 border border-danger/30 rounded-lg flex items-center gap-3 text-danger">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {/* НАВИГАЦИЯ ПО РАЗДЕЛАМ (ТАБЫ) */}
          <div className="flex items-center gap-2.5 p-1.5 bg-gray-900/90 border border-gray-800 rounded-2xl mb-8 overflow-x-auto shadow-md">
            <button
              onClick={() => setActiveTab('upcoming')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap ${
                activeTab === 'upcoming'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25 ring-1 ring-blue-400/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Flame className="w-4 h-4 text-amber-400" />
              <span>Топ Ставки Дня</span>
            </button>

            <button
              onClick={() => setActiveTab('archive')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap ${
                activeTab === 'archive'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/25 ring-1 ring-emerald-400/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Архив счетов (Проверка)</span>
            </button>

            <button
              onClick={() => setActiveTab('stats')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap ${
                activeTab === 'stats'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/25 ring-1 ring-purple-400/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Trophy className="w-4 h-4 text-yellow-400" />
              <span>Рейтинг & Проходимость</span>
            </button>
          </div>

          {/* ВЫБРАННЫЙ РАЗДЕЛ 1: ПРЕДСТОЯЩИЕ ТОП-СТАВКИ */}
          {activeTab === 'upcoming' && (
            <>
              {/* Секция Топ Ставок */}
              <section className="mb-12">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div className="flex items-center gap-2">
                    <Flame className="w-6 h-6 text-accent" />
                    <h2 className="text-xl font-bold text-gray-200">Главные консенсусы дня</h2>
                  </div>
                  
                  {topBets.length > 0 && (
                    <button 
                      onClick={handleAiAnalysis}
                      disabled={isAiLoading}
                      className="group relative flex items-center gap-2 bg-gradient-to-r from-blue-600 via-accent to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-5 py-2.5 rounded-xl font-bold transition-all disabled:opacity-50 overflow-hidden shadow-lg shadow-blue-500/25"
                    >
                      <div className="absolute inset-0 w-full h-full bg-white/20 group-hover:scale-x-100 scale-x-0 origin-left transition-transform duration-300"></div>
                      <Bot className={`w-5 h-5 relative z-10 ${isAiLoading ? 'animate-bounce' : ''}`} />
                      <span className="relative z-10">{isAiLoading ? 'Нейросеть думает...' : 'Получить Супер-Анализ 🚀'}</span>
                    </button>
                  )}
                </div>

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

                {loading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-64 bg-card rounded-xl border border-gray-800 animate-pulse"></div>
                    ))}
                  </div>
                ) : topBets.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
                    {topBets.map(bet => (
                      <TopBetCard key={bet.match_id + bet.recommended_outcome} bet={bet} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-card rounded-xl border border-gray-800 text-gray-500">
                    {error ? "Ошибка загрузки" : "На сегодня нет уверенных ставок для этой категории."}
                  </div>
                )}
              </section>

              {/* Секция Всех Матчей */}
              <section>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div className="flex items-center gap-2">
                    <CalendarDays className="w-6 h-6 text-gray-400" />
                    <h2 className="text-xl font-bold text-gray-200">Линия матчей</h2>
                  </div>
                  
                  <input 
                    type="date" 
                    value={currentDate}
                    onChange={(e) => setCurrentDate(e.target.value)}
                    className="bg-card text-white border border-gray-700 rounded-lg px-4 py-2 outline-none focus:border-accent"
                  />
                </div>
                
                <div className="bg-card rounded-xl border border-gray-800 overflow-hidden shadow-sm">
                  {loading ? (
                    <div className="p-8 text-center text-gray-500 animate-pulse">Загрузка расписания...</div>
                  ) : (
                    <MatchList matches={matches} />
                  )}
                </div>
              </section>
            </>
          )}

          {/* ВЫБРАННЫЙ РАЗДЕЛ 2: АРХИВ ЗАВЕРШЁННЫХ МАТЧЕЙ И СЧЕТА */}
          {activeTab === 'archive' && (
            <section className="space-y-6 animate-fade-in">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                    <span>Архив завершённых матчей</span>
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Финальные счета и верификация проходимости ставок
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

          {/* ВЫБРАННЫЙ РАЗДЕЛ 3: РЕЙТИНГ КАППЕРОВ И СТАТИСТИКА */}
          {activeTab === 'stats' && (
            <StatsLeaderboard />
          )}

        </main>
      </div>

      <footer className="border-t border-gray-800 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
          &copy; {new Date().getFullYear()} AI Sports Aggregator. Данные носят рекомендательный характер.
        </div>
      </footer>
    </div>
  );
}

export default App;
