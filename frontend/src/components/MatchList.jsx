import React from 'react';
import TeamBadge from './TeamBadge';
import { toRussianTeam, toRussianLeague } from '../utils/russianNames';

const MatchList = ({ matches }) => {
  if (!matches || matches.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 bg-card rounded-xl border border-gray-800">
        Нет доступных матчей на сегодня для выбранного спорта.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-800 text-gray-400 text-xs sm:text-sm uppercase tracking-wider font-heading">
            <th className="py-4 px-4 font-black">Время</th>
            <th className="py-4 px-4 font-black">Матч</th>
            <th className="py-4 px-4 font-black">Лига / Турнир</th>
            <th className="py-4 px-4 font-black text-right">Прогнозы</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800/50">
          {matches.map((match) => {
            const homeRu = toRussianTeam(match.home_team);
            const awayRu = toRussianTeam(match.away_team);
            const leagueRu = toRussianLeague(match.league);

            return (
              <tr key={match.id} className="hover:bg-gray-800/30 transition-colors group">
                <td className="py-4 px-4 text-xs sm:text-sm text-gray-400 whitespace-nowrap font-mono">
                  {new Date(match.match_date).toLocaleString('ru-RU', {
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit',
                    timeZone: 'Europe/Moscow'
                  })}
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center gap-3">
                    {/* Хозяева */}
                    <div className="flex items-center gap-2.5 w-[45%] justify-end">
                      <span className="font-black text-base sm:text-lg text-white text-right truncate font-heading tracking-tight drop-shadow-sm group-hover:text-blue-300 transition-colors">
                        {homeRu}
                      </span>
                      <TeamBadge teamName={homeRu} logoUrl={match.home_logo} size="sm" />
                    </div>
                    
                    {/* Разделитель VS или счет */}
                    {match.final_score_home !== null && match.final_score_away !== null ? (
                      <span className="px-2.5 py-1 rounded-xl bg-gray-800 text-xs font-black text-emerald-400 border border-emerald-500/30 font-mono shadow-inner">
                        {match.final_score_home}:{match.final_score_away}
                      </span>
                    ) : (
                      <span className="text-xs font-black text-gray-500 italic px-1 font-heading">VS</span>
                    )}
                    
                    {/* Гости */}
                    <div className="flex items-center gap-2.5 w-[45%]">
                      <TeamBadge teamName={awayRu} logoUrl={match.away_logo} size="sm" />
                      <span className="font-black text-base sm:text-lg text-white truncate font-heading tracking-tight drop-shadow-sm group-hover:text-blue-300 transition-colors">
                        {awayRu}
                      </span>
                    </div>
                  </div>
                </td>
                <td className="py-4 px-4 text-xs sm:text-sm font-semibold text-gray-300 truncate max-w-[220px]">
                  {leagueRu}
                </td>
                <td className="py-4 px-4 text-right">
                  <span className="inline-flex items-center justify-center px-3 py-1 bg-blue-500/10 text-blue-300 text-xs font-black rounded-full border border-blue-500/30 group-hover:bg-blue-500/20 transition-colors shadow-sm">
                    {match.predictions?.length || 0} мнений
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default MatchList;
