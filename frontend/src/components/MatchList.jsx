import React from 'react';

const MatchList = ({ matches }) => {
  if (!matches || matches.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 bg-card rounded-xl border border-gray-800">
        Нет доступных матчей на сегодня для выбранного спорта.
      </div>
    );
  }

  const getLogoUrl = (teamName) => 
    `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName || 'Team')}&background=random&color=fff&size=32&bold=true&rounded=true`;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-800 text-gray-400 text-sm uppercase tracking-wider">
            <th className="py-4 px-4 font-semibold">Время</th>
            <th className="py-4 px-4 font-semibold">Матч</th>
            <th className="py-4 px-4 font-semibold">Лига</th>
            <th className="py-4 px-4 font-semibold text-right">Прогнозы</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800/50">
          {matches.map((match) => (
            <tr key={match.id} className="hover:bg-gray-800/30 transition-colors group">
              <td className="py-4 px-4 text-sm text-gray-400 whitespace-nowrap">
                {new Date(match.match_date).toLocaleString([], {month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'})}
              </td>
              <td className="py-4 px-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 w-[45%] justify-end">
                    <span className="font-semibold text-gray-200 text-right truncate">{match.home_team}</span>
                    <img src={getLogoUrl(match.home_team)} alt="home" className="w-8 h-8 rounded-full ring-1 ring-gray-700" />
                  </div>
                  
                  <span className="text-xs font-black text-gray-600 italic px-2">VS</span>
                  
                  <div className="flex items-center gap-2 w-[45%]">
                    <img src={getLogoUrl(match.away_team)} alt="away" className="w-8 h-8 rounded-full ring-1 ring-gray-700" />
                    <span className="font-semibold text-gray-200 truncate">{match.away_team}</span>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4 text-sm text-gray-400 truncate max-w-[200px]">{match.league}</td>
              <td className="py-4 px-4 text-right">
                <span className="inline-flex items-center justify-center px-3 py-1 bg-blue-500/10 text-blue-400 text-xs font-bold rounded-full border border-blue-500/20 group-hover:bg-blue-500/20 transition-colors">
                  {match.predictions?.length || 0} мнений
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MatchList;
