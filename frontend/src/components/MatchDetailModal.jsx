import React, { useState } from 'react';
import { 
  X, Target, Shield, Sparkles, Brain, TrendingUp, Users, 
  MessageSquare, Flame, BookOpen, Swords, BarChart3, CheckCircle2 
} from 'lucide-react';

const formatOutcome = (outcome) => {
  if (!outcome) return '';
  const map = {
    'home_win': 'Победа Хозяев (П1)',
    'away_win': 'Победа Гостей (П2)',
    'draw': 'Ничья (Х)',
    'total_over_2.5': 'Тотал Больше 2.5',
    'total_under_2.5': 'Тотал Меньше 2.5'
  };
  if (map[outcome]) return map[outcome];
  if (outcome.includes(' ') || outcome.includes('(')) return outcome;
  return outcome.replace(/_/g, ' ').toUpperCase();
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

const MatchDetailModal = ({ bet, onClose }) => {
  if (!bet) return null;

  const [activeTab, setActiveTab] = useState('sources'); // 'sources', 'tactics', 'ai'

  const [homeTeam, awayTeam] = bet.match_name.includes(' vs ')
    ? bet.match_name.split(' vs ')
    : bet.match_name.split(' - ');

  const getLogoUrl = (teamName) =>
    `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName || 'Team')}&background=random&color=fff&size=80&bold=true&rounded=true`;

  const predictions = bet.all_predictions || [];

  // Подсчет распределения исходов
  const outcomesCount = {};
  predictions.forEach(p => {
    const out = formatOutcome(p.predicted_outcome);
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
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className="text-xs font-bold px-3 py-1 bg-blue-500/15 text-blue-400 rounded-full border border-blue-500/30 uppercase tracking-wider">
              {bet.sport_type}
            </span>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-gray-800 text-gray-300 rounded-md border border-gray-700">
              {bet.league}
            </span>
            {bet.is_bet_of_the_day && (
              <span className="text-xs font-black text-yellow-400 bg-yellow-400/15 px-3 py-1 rounded-md border border-yellow-400/30 flex items-center gap-1 animate-pulse">
                🏆 {getRussianSport(bet.sport_type)} - СТАВКА ДНЯ
              </span>
            )}
          </div>

          {/* Команды и время матча */}
          <div className="flex items-center justify-between gap-4 mt-3">
            <div className="flex flex-col items-center flex-1 text-center">
              <img src={getLogoUrl(homeTeam)} alt={homeTeam} className="w-16 h-16 rounded-full mb-2 ring-2 ring-blue-500/40 shadow-lg object-cover" />
              <h3 className="font-bold text-white text-base leading-tight">{homeTeam}</h3>
              <span className="text-[11px] text-gray-400 mt-0.5">Хозяева</span>
            </div>

            <div className="flex flex-col items-center justify-center px-2">
              <div className="px-3.5 py-1.5 bg-gray-800/90 rounded-2xl border border-gray-700 text-center mb-1 shadow-inner">
                <span className="text-[11px] text-gray-400 block font-semibold">
                  {new Date(bet.match_date).toLocaleString([], {month: 'short', day: 'numeric'})}
                </span>
                <span className="text-lg font-black text-white">
                  {new Date(bet.match_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
              </div>
              <span className="text-xs font-black text-gray-500 italic">VS</span>
            </div>

            <div className="flex flex-col items-center flex-1 text-center">
              <img src={getLogoUrl(awayTeam)} alt={awayTeam} className="w-16 h-16 rounded-full mb-2 ring-2 ring-purple-500/40 shadow-lg object-cover" />
              <h3 className="font-bold text-white text-base leading-tight">{awayTeam}</h3>
              <span className="text-[11px] text-gray-400 mt-0.5">Гости</span>
            </div>
          </div>

          {/* Главный консенсус плашка */}
          <div className="mt-5 p-4 bg-gradient-to-r from-blue-950/60 via-indigo-950/40 to-gray-900 rounded-2xl border border-blue-500/30 shadow-inner flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-500/20 rounded-xl text-blue-400 shrink-0">
                <Target className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider text-blue-300 font-bold block">
                  Главный консенсус алгоритма
                </span>
                <span className="text-lg font-black text-white leading-tight">
                  {formatOutcome(bet.recommended_outcome)}
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
                            <span className="font-black text-emerald-400 text-sm block">
                              {formatOutcome(p.predicted_outcome)}
                            </span>
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
