import React from 'react';
import { Target, TrendingUp, Users, Shield } from 'lucide-react';

const formatOutcome = (outcome) => {
  const map = {
    'home_win': 'Победа Хозяев (П1)',
    'away_win': 'Победа Гостей (П2)',
    'draw': 'Ничья (Х)',
    'total_over_2.5': 'Тотал Больше 2.5'
  };
  
  if (map[outcome]) return map[outcome];
  
  // Если исход пришел текстом из парсера (например "Фора 1 (-1.5)"), просто отдаем как есть
  if (outcome.includes(' ') || outcome.includes('(')) {
    return outcome;
  }
  
  return outcome.replace(/_/g, ' ').toUpperCase();
};

const TopBetCard = ({ bet }) => {
  let colorClass = 'bg-accent';
  let textClass = 'text-accent';
  let shadowClass = 'shadow-blue-500/20 border-accent/20';
  
  if (bet.confidence_score >= 80) {
    colorClass = 'bg-success';
    textClass = 'text-success';
    shadowClass = 'shadow-green-500/20 border-success/20';
  } else if (bet.confidence_score < 60) {
    colorClass = 'bg-warning';
    textClass = 'text-warning';
    shadowClass = 'shadow-yellow-500/20 border-warning/20';
  }

  // Извлекаем названия команд
  const [homeTeam, awayTeam] = bet.match_name.includes(' vs ') 
    ? bet.match_name.split(' vs ') 
    : bet.match_name.split(' - ');

  // Генерируем красивые эмблемы (заглушки) по названиям команд
  const getLogoUrl = (teamName) => 
    `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName || 'Team')}&background=random&color=fff&size=64&bold=true&rounded=true`;

  const getRussianSport = (sport) => {
    const s = (sport || '').toLowerCase();
    if (s.includes('soccer') || s.includes('liga') || s.includes('epl') || s.includes('football') || s.includes('premier') || s.includes('championship') || s.includes('serie')) return 'ФУТБОЛ';
    if (s.includes('nba') || s.includes('basketball')) return 'БАСКЕТБОЛ';
    if (s.includes('nhl') || s.includes('hockey') || s.includes('khl')) return 'ХОККЕЙ';
    if (s.includes('tennis') || s.includes('atp') || s.includes('wta')) return 'ТЕННИС';
    return 'СПОРТ';
  };

  return (
    <div className={`bg-card rounded-2xl p-6 border ${shadowClass} shadow-lg hover:-translate-y-2 transition-all duration-300 relative overflow-hidden group`}>
      {/* Декоративный фон */}
      <div className={`absolute top-0 right-0 w-32 h-32 opacity-5 rounded-bl-full ${colorClass}`}></div>

      <div className="flex justify-between items-start mb-6 relative z-10">
        <div className="flex flex-col gap-2">
          <span className="text-xs font-bold px-3 py-1 bg-gray-800 text-gray-300 rounded-full uppercase tracking-widest border border-gray-700 w-fit whitespace-nowrap">
            {bet.sport_type}
          </span>
          {bet.is_bet_of_the_day && (
            <span className="inline-flex items-center gap-1 text-xs font-extrabold text-yellow-400 bg-yellow-400/10 px-3 py-1 rounded-md border border-yellow-400/30 animate-pulse w-fit whitespace-nowrap">
              🏆 {getRussianSport(bet.sport_type)} - СТАВКА ДНЯ
            </span>
          )}
        </div>

        {/* Дата и время */}
        {bet.match_date && (
          <div className="flex flex-col items-center bg-gray-900/80 px-4 py-2 rounded-xl border border-gray-700 shadow-inner">
            <span className="text-[10px] text-gray-400 uppercase font-bold tracking-wider mb-0.5 whitespace-nowrap">
              {new Date(bet.match_date).toLocaleString([], {month: 'long', day: 'numeric'})}
            </span>
            <span className="text-xl font-black text-white leading-none">
              {new Date(bet.match_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </span>
          </div>
        )}
      </div>

      {/* Versus Layout с логотипами */}
      <div className="flex items-center justify-between mb-6 gap-2">
        <div className="flex flex-col items-center flex-1 text-center">
          <img src={getLogoUrl(homeTeam)} alt={homeTeam} className="w-12 h-12 rounded-full mb-2 ring-2 ring-gray-800 group-hover:ring-gray-600 transition-all" />
          <span className="text-sm font-bold text-gray-200 line-clamp-2 leading-tight">{homeTeam}</span>
        </div>
        
        <div className="flex flex-col items-center justify-center px-2">
          <span className="text-xs font-black text-gray-600 italic">VS</span>
        </div>

        <div className="flex flex-col items-center flex-1 text-center">
          <img src={getLogoUrl(awayTeam)} alt={awayTeam} className="w-12 h-12 rounded-full mb-2 ring-2 ring-gray-800 group-hover:ring-gray-600 transition-all" />
          <span className="text-sm font-bold text-gray-200 line-clamp-2 leading-tight">{awayTeam}</span>
        </div>
      </div>

      {/* Уверенность алгоритма */}
      <div className="mb-5 bg-dark/50 p-3 rounded-xl border border-gray-800/50">
        <div className="flex justify-between text-xs mb-2">
          <span className="text-gray-400 font-medium">Консенсус Капперов</span>
          <span className={`font-black ${textClass}`}>{bet.confidence_score}%</span>
        </div>
        <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
          <div 
            className={`h-full ${colorClass} transition-all duration-1000 ease-out`} 
            style={{ width: `${bet.confidence_score}%` }}
          ></div>
        </div>
      </div>

      {/* Исход с коэффициентом */}
      <div className={`flex items-center justify-between p-4 rounded-xl mb-4 border ${shadowClass.replace('shadow-', 'bg-').replace('/20', '/5')}`}>
        <div className="flex items-center gap-4">
          <div className={`p-2 rounded-lg ${colorClass} bg-opacity-20 shrink-0`}>
            <Target className={`w-6 h-6 ${textClass}`} />
          </div>
          <div>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold mb-1">Исход</p>
            <p className="font-extrabold text-white text-base leading-tight">{formatOutcome(bet.recommended_outcome)}</p>
          </div>
        </div>
        
        <div className="text-right pl-4 border-l border-gray-700/50 shrink-0">
          <div className="text-2xl font-black text-white">{bet.average_odds.toFixed(2)}</div>
          <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mt-0.5">КЭФ</p>
        </div>
      </div>

      <div className="flex items-start gap-3 text-xs text-gray-400 bg-gray-900/50 p-3 rounded-lg mb-4">
        <Shield className="w-4 h-4 mt-0.5 shrink-0 text-gray-500" />
        <p className="leading-relaxed">
          <span className="font-semibold text-gray-300">Подтверждено:</span> {bet.supporting_sources.join(', ')}
        </p>
      </div>

      {bet.cappers_reasoning && (
        <div className="mb-4 p-4 bg-gray-800/40 rounded-xl border border-gray-700/50">
          <h4 className="text-[11px] uppercase tracking-wider text-gray-500 font-bold mb-2">Общая мысль капперов</h4>
          <p className="text-sm text-gray-300 leading-relaxed">
            {bet.cappers_reasoning}
          </p>
        </div>
      )}

      {bet.ai_insight && (
        <div className="mt-2 p-3 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-xl border border-blue-500/20 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-400 to-purple-500"></div>
          <p className="text-sm text-gray-200 leading-relaxed italic pl-2">
            <span className="font-bold text-blue-400 mr-2">ИИ:</span> 
            {bet.ai_insight}
          </p>
        </div>
      )}
    </div>
  );
};

export default TopBetCard;
