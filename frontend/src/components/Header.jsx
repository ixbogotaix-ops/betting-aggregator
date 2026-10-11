import React, { useState, useEffect } from 'react';
import { Trophy, Activity, Target, Clock } from 'lucide-react';

const sports = ['All', 'Football', 'Hockey', 'Basketball', 'Esports'];

const MoscowClock = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Format to Moscow Time
  const optionsTime = { timeZone: 'Europe/Moscow', hour: '2-digit', minute: '2-digit', second: '2-digit' };
  const optionsDate = { timeZone: 'Europe/Moscow', day: 'numeric', month: 'long', year: 'numeric' };
  
  const timeString = time.toLocaleTimeString('ru-RU', optionsTime);
  const dateString = time.toLocaleDateString('ru-RU', optionsDate);

  return (
    <div className="hidden lg:flex flex-col items-end justify-center bg-gray-800/40 border border-gray-700/50 rounded-xl px-4 py-1.5 shadow-inner">
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-accent" />
        <span className="text-xl font-black text-white tracking-wider font-mono">{timeString}</span>
      </div>
      <span className="text-xs font-medium text-gray-400 uppercase tracking-widest">Москва • {dateString}</span>
    </div>
  );
};

const Header = ({ currentSport, onSportChange }) => {
  return (
    <header className="bg-dark border-b border-gray-800 sticky top-0 z-50">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-xl">
              <Trophy className="w-7 h-7 text-accent" />
            </div>
            <h1 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500 tracking-tight">
              AI Sports Aggregator
            </h1>
          </div>

          {/* Navigation/Filters */}
          <nav className="flex space-x-2 overflow-x-auto mx-4 hidden md:flex">
            {sports.map((sport) => (
              <button
                key={sport}
                onClick={() => onSportChange(sport)}
                className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all whitespace-nowrap uppercase tracking-wider
                  ${currentSport === sport 
                    ? 'bg-accent text-white shadow-lg shadow-blue-500/25 ring-1 ring-blue-400/50' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-800 ring-1 ring-transparent hover:ring-gray-700'
                  }`}
              >
                {sport}
              </button>
            ))}
          </nav>

          {/* Moscow Clock */}
          <MoscowClock />
        </div>
      </div>
    </header>
  );
};

export default Header;
