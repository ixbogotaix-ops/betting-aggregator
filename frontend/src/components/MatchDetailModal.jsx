import React from 'react';
import { X, Target, Shield, Sparkles, Brain, TrendingUp, Users, ExternalLink, Award } from 'lucide-react';

const formatOutcome = (outcome) => {
  const map = {
    'home_win': 'Победа Хозяев (П1)',
    'away_win': 'Победа Гостей (П2)',
    'draw': 'Ничья (Х)',
    'total_over_2.5': 'Тотал Больше 2.5'
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

  const [homeTeam, awayTeam] = bet.match_name.includes(' vs ')
    ? bet.match_name.split(' vs ')
    : bet.match_name.split(' - ');

  const getLogoUrl = (teamName) =>
    `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName || 'Team')}&background=random&color=fff&size=80&bold=true&rounded=true`;

  const predictions = bet.all_predictions || [];

  // Группировка прогнозов по исходам для наглядного распределения голосов
  const outcomesCount = {};
  predictions.forEach(p => {
    const out = p.predicted_outcome;
    outcomesCount[out] = (outcomesCount[out] || 0) + 1;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div 
        className="relative w-full max-w-2xl bg-gray-900 border border-gray-700/80 rounded-3xl shadow-2xl overflow-hidden my-auto max-h-[92vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 text-gray-400 hover:text-white bg-gray-800/80 hover:bg-gray-700 rounded-full transition-all border border-gray-700"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Шапка модалки */}
        <div className="p-6 bg-gradient-to-b from-gray-800/60 to-gray-900/40 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-bold px-3 py-1 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20 uppercase tracking-wider">
              {bet.sport_type}
            </span>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-gray-800 text-gray-400 rounded-md border border-gray-700">
              {bet.league}
            </span>
            {bet.is_bet_of_the_day && (
              <span className="text-xs font-black text-yellow-400 bg-yellow-400/10 px-3 py-1 rounded-md border border-yellow-400/30 flex items-center gap-1 animate-pulse">
                🏆 {getRussianSport(bet.sport_type)} - СТАВКА ДНЯ
              </span>
            )}
          </div>

          {/* Команды и время */}
          <div className="flex items-center justify-between gap-4 mt-4">
            <div className="flex flex-col items-center flex-1 text-center">
              <img src={getLogoUrl(homeTeam)} alt={homeTeam} className="w-16 h-16 rounded-full mb-2 ring-2 ring-blue-500/30 shadow-lg" />
              <h3 className="font-bold text-white text-base leading-tight">{homeTeam}</h3>
              <span className="text-[11px] text-gray-400 mt-0.5">Хозяева</span>
            </div>

            <div className="flex flex-col items-center justify-center px-2">
              <div className="px-3 py-1 bg-gray-800/90 rounded-xl border border-gray-700 text-center mb-1">
                <span className="text-[10px] text-gray-400 block font-semibold">
                  {new Date(bet.match_date).toLocaleString([], {month: 'short', day: 'numeric'})}
                </span>
                <span className="text-lg font-black text-white">
                  {new Date(bet.match_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
              </div>
              <span className="text-xs font-black text-gray-600 italic">VS</span>
            </div>

            <div className="flex flex-col items-center flex-1 text-center">
              <img src={getLogoUrl(awayTeam)} alt={awayTeam} className="w-16 h-16 rounded-full mb-2 ring-2 ring-purple-500/30 shadow-lg" />
              <h3 className="font-bold text-white text-base leading-tight">{awayTeam}</h3>
              <span className="text-[11px] text-gray-400 mt-0.5">Гости</span>
            </div>
          </div>
        </div>

        {/* Прокручиваемый контент */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 custom-scrollbar">
          {/* Главный консенсус */}
          <div className="p-4 bg-gradient-to-r from-blue-950/40 via-gray-900 to-indigo-950/40 rounded-2xl border border-blue-500/30 shadow-inner flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-500/20 rounded-xl text-blue-400">
                <Target className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider text-gray-400 font-bold block">
                  Главный консенсус алгоритма
                </span>
                <span className="text-lg font-black text-white leading-tight">
                  {formatOutcome(bet.recommended_outcome)}
                </span>
              </div>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black text-emerald-400">{bet.average_odds.toFixed(2)}</span>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest block font-bold">КЭФ</span>
            </div>
          </div>

          {/* Шкала консенсуса */}
          <div className="bg-gray-800/40 p-4 rounded-xl border border-gray-700/50">
            <div className="flex justify-between items-center text-xs mb-2">
              <span className="text-gray-300 font-semibold flex items-center gap-1.5">
                <Users className="w-4 h-4 text-blue-400" /> Уверенность аналитического ядра
              </span>
              <span className="font-black text-blue-400 text-sm">{bet.confidence_score}%</span>
            </div>
            <div className="h-2.5 w-full bg-gray-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 transition-all duration-1000" 
                style={{ width: `${bet.confidence_score}%` }}
              ></div>
            </div>
          </div>

          {/* Вердикт ИИ */}
          {bet.ai_insight && (
            <div className="p-4 bg-gradient-to-r from-blue-900/30 via-purple-900/20 to-gray-900 rounded-2xl border border-blue-500/30 relative">
              <div className="flex items-center gap-2 mb-2 text-blue-400 font-bold text-xs">
                <Sparkles className="w-4 h-4" />
                <span>ИНСАЙТ НЕЙРОСЕТИ</span>
              </div>
              <p className="text-sm text-gray-200 leading-relaxed italic">
                {bet.ai_insight}
              </p>
            </div>
          )}

          {/* Логика капперов */}
          {bet.cappers_reasoning && (
            <div className="p-4 bg-gray-800/50 rounded-2xl border border-gray-700/60">
              <div className="flex items-center gap-2 mb-2 text-gray-400 font-bold text-xs uppercase tracking-wider">
                <Brain className="w-4 h-4 text-indigo-400" />
                <span>Сводный анализ экспертов</span>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">
                {bet.cappers_reasoning}
              </p>
            </div>
          )}

          {/* КТО И КУДА СТАВИТ (Детальный список всех капперов) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span>Кто и куда ставит ({predictions.length} прогнозов):</span>
              </h4>
              <span className="text-xs text-gray-400">Сводка источников</span>
            </div>

            {predictions.length > 0 ? (
              <div className="space-y-2">
                {predictions.map((p, idx) => (
                  <div 
                    key={idx}
                    className="p-3.5 bg-gray-800/70 hover:bg-gray-800 rounded-xl border border-gray-700/60 transition-all flex items-center justify-between gap-3 text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 flex-1">
                      <span className="text-base shrink-0">
                        {p.source_type === 'telegram_channel' ? '📡' : '🌐'}
                      </span>
                      <div className="min-w-0">
                        <span className="font-bold text-white block truncate text-sm">
                          {p.source_name}
                        </span>
                        <div className="flex items-center gap-2 text-[11px] text-gray-400 mt-0.5">
                          <span>{p.source_type === 'telegram_channel' ? 'Telegram Канал' : 'Аналитический Портал'}</span>
                          {p.source_weight && (
                            <span className="text-amber-400 font-semibold bg-amber-400/10 px-1.5 py-0.2 rounded border border-amber-400/20">
                              Вес: {p.source_weight}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="font-black text-emerald-400 text-sm block">
                        {p.predicted_outcome}
                      </span>
                      <span className="text-[11px] text-gray-400 font-bold">
                        Кэф: <strong className="text-white">{p.odds}</strong>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-gray-800/30 rounded-xl border border-gray-800 text-center text-xs text-gray-400">
                Подтверждено источниками: <strong className="text-gray-200">{bet.supporting_sources.join(', ')}</strong>
              </div>
            )}
          </div>
        </div>

        {/* Подвал модалки */}
        <div className="p-4 bg-gray-900 border-t border-gray-800 text-center text-xs text-gray-500 shrink-0">
          Данные агрегированы с 52 источников в режиме реального времени
        </div>
      </div>
    </div>
  );
};

export default MatchDetailModal;
