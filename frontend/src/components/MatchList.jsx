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

            const hasScore = match.final_score_home !== null && match.final_score_away !== null;
            const isMatchFinished = match.status === 'finished' || hasScore;
            const isMatchLive = !isMatchFinished && (
              match.status === 'live' || 
              (() => {
                try {
                  const start = new Date(match.match_date).getTime();
                  const now = Date.now();
                  return now >= start && (now - start) < (2.5 * 3600 * 1000);
                } catch (e) { return false; }
              })()
            );

            return (
              <tr key={match.id} className="hover:bg-gray-800/30 transition-colors group">
                <td className="py-4 px-4 text-xs sm:text-sm whitespace-nowrap font-mono">
                  {isMatchLive ? (
                    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-red-950/80 border border-red-500/50 text-[10px] font-black text-red-300 animate-pulse">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping"></span>
                      <span>LIVE</span>
                    </div>
                  ) : isMatchFinished ? (
                    <span className="text-[10px] font-extrabold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded-lg border border-emerald-500/30">
                      ФИНАЛ
                    </span>
                  ) : (
                    <span className="text-gray-400">
                      {new Date(match.match_date).toLocaleString('ru-RU', {
                        month: 'short', 
                        day: 'numeric', 
                        hour: '2-digit', 
                        minute: '2-digit',
                        timeZone: 'Europe/Moscow'
                      })}
                    </span>
                  )}
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
                    {hasScore ? (
                      <span className={`px-2.5 py-1 rounded-xl text-xs font-black font-mono shadow-inner border ${
                        isMatchLive ? 'bg-red-950/90 text-white border-red-500/60 animate-pulse' : 'bg-gray-800 text-emerald-400 border-emerald-500/30'
                      }`}>
                        {match.final_score_home}:{match.final_score_away}
                      </span>
                    ) : isMatchLive ? (
                      <span className="px-2 py-0.5 rounded-lg bg-red-950/80 text-[10px] font-black text-red-300 border border-red-500/40 animate-pulse font-mono">
                        LIVE
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
