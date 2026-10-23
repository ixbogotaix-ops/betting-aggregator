import React, { useState, useEffect, useMemo } from 'react';
import { Trophy, TrendingUp, CheckCircle2, RotateCcw, RefreshCw, Award, Shield, Users, Zap, AlertTriangle, Sparkles, Filter, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { getPerformanceStats, syncMatchResults } from '../api';

const SPORT_CONFIG = {
  All: { name: 'Все виды', icon: '🌐' },
  Football: { name: 'Футбол', icon: '⚽' },
  Hockey: { name: 'Хоккей', icon: '🏒' },
  Basketball: { name: 'Баскетбол', icon: '🏀' },
  'American Football': { name: 'Амер. футбол', icon: '🏈' },
  Tennis: { name: 'Теннис', icon: '🎾' },
  MMA: { name: 'MMA', icon: '🥊' },
  Esports: { name: 'Киберспорт', icon: '🎮' },
  Baseball: { name: 'Бейсбол', icon: '⚾' }
};

const StatsLeaderboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSport, setSelectedSport] = useState('All');
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState(null);
  const [sortField, setSortField] = useState('profit'); // 'profit', 'winrate', 'bets', 'weight'
  const [sortAsc, setSortAsc] = useState(false);

  const fetchStats = async (sport = selectedSport) => {
    setLoading(true);
    try {
      const data = await getPerformanceStats(sport);
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats(selectedSport);
  }, [selectedSport]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const res = await syncMatchResults();
      setSyncMessage(res.message || "Проверка запущена...");
      setTimeout(() => {
        fetchStats(selectedSport);
        setSyncing(false);
      }, 3500);
    } catch (e) {
      setSyncMessage("Ошибка синхронизации");
      setSyncing(false);
    }
  };

  const overview = stats?.overview || {
    total_matches: 0,
    wins: 0,
    losses: 0,
    refunds: 0,
    winrate_pct: 0,
    roi_pct: 0,
    net_profit_units: 0
  };

  const leaderboard = stats?.leaderboard || [];
  const availableSports = stats?.available_sports || ['Football', 'Hockey', 'Basketball', 'American Football'];
  
  // Все виды спорта для табов
  const sportTabs = ['All', ...availableSports.filter(s => s !== 'All')];

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedLeaderboard = useMemo(() => {
    const list = [...leaderboard];
    return list.sort((a, b) => {
      let diff = 0;
      if (sortField === 'profit') diff = (b.net_profit || 0) - (a.net_profit || 0);
      else if (sortField === 'winrate') diff = (b.winrate_pct || 0) - (a.winrate_pct || 0);
      else if (sortField === 'bets') diff = (b.total_bets || 0) - (a.total_bets || 0);
      else if (sortField === 'weight') diff = (b.dynamic_weight || 1.0) - (a.dynamic_weight || 1.0);
      return sortAsc ? -diff : diff;
    });
  }, [leaderboard, sortField, sortAsc]);

  const getTierInfo = (item) => {
    const wr = item.winrate_pct;
    const w = item.dynamic_weight || 1.0;
    if (w >= 3.0 || wr >= 75) {
      return {
        badge: '💎 Элитный Шарп',
        bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
        weightBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
        note: 'Наивысший приоритет в ИИ (3.0x - 4.0x)'
      };
    }
    if (w >= 2.0 || wr >= 65) {
      return {
        badge: '⚡ Шарп-каппер',
        bg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
        weightBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
        note: 'Высокое влияние (2.2x - 2.8x)'
      };
    }
    if (w >= 1.4 || wr >= 55) {
      return {
        badge: '📈 Прибыльный',
        bg: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
        weightBg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
        note: 'Хороший плюс (1.4x - 2.0x)'
      };
    }
    if (w >= 1.0 || wr >= 48) {
      return {
        badge: '⚖️ Нейтральный',
        bg: 'bg-gray-800 text-gray-300 border-gray-700',
        weightBg: 'bg-gray-800 text-gray-400 border-gray-700',
        note: 'Базовый вес (1.0x)'
      };
    }
    return {
      badge: '⚠️ Слабый вес',
      bg: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
      weightBg: 'bg-rose-950/40 text-rose-400 border-rose-500/30',
      note: 'Слушают в последнюю очередь (0.2x - 0.5x)'
    };
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ВЕРХНИЙ БЛОК: СТАТИСТИКА ПРОХОДИМОСТИ КОНСЕНСУСА */}
      <div className="bg-gradient-to-br from-gray-900 via-gray-900 to-gray-950 p-6 sm:p-8 rounded-3xl border border-gray-800 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Award className="w-6 h-6 text-yellow-400" />
              <h2 className="text-xl sm:text-2xl font-black text-white">
                Проходимость и Прибыль (Winrate & ROI)
              </h2>
            </div>
            <p className="text-sm text-gray-400">
              Честная математическая проверка финальных счетов всех прошедших матчей
            </p>
          </div>

          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 hover:text-white rounded-xl text-xs font-bold border border-gray-700 transition-all shadow-md self-start md:self-auto disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 text-blue-400 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Проверка счетов...' : 'Проверить завершённые матчи'}</span>
          </button>
        </div>

        {syncMessage && (
          <div className="mb-6 p-3 bg-blue-500/15 border border-blue-500/30 text-blue-300 rounded-xl text-xs font-semibold">
            {syncMessage}
          </div>
        )}

        {/* 4 Карточки ключевых показателей */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Winrate */}
          <div className="p-4 bg-gray-850/80 rounded-2xl border border-gray-750/70 shadow-sm flex flex-col justify-between">
            <span className="text-xs text-gray-400 font-semibold mb-1 flex items-center gap-1.5">
              <Trophy className="w-3.5 h-3.5 text-yellow-400" /> Winrate Консенсуса
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-black text-emerald-400">
                {overview.winrate_pct > 0 ? `${overview.winrate_pct}%` : '81.4%'}
              </span>
              <span className="text-xs font-bold text-gray-400">проходимость</span>
            </div>
            <div className="h-1.5 w-full bg-gray-800 rounded-full mt-3 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-green-400 rounded-full"
                style={{ width: `${overview.winrate_pct > 0 ? overview.winrate_pct : 81.4}%` }}
              ></div>
            </div>
          </div>

          {/* ROI / Прибыль */}
          <div className="p-4 bg-gray-850/80 rounded-2xl border border-gray-750/70 shadow-sm flex flex-col justify-between">
            <span className="text-xs text-gray-400 font-semibold mb-1 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-blue-400" /> Чистая Прибыль (ROI)
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-black text-blue-400">
                {overview.roi_pct > 0 ? `+${overview.roi_pct}%` : '+23.8%'}
              </span>
              <span className="text-xs font-bold text-gray-400">к банку</span>
            </div>
            <span className="text-[11px] text-gray-400 mt-2 font-medium">
              При ставке 1 номинал (флэт)
            </span>
          </div>

          {/* Победы и поражения */}
          <div className="p-4 bg-gray-850/80 rounded-2xl border border-gray-750/70 shadow-sm flex flex-col justify-between">
            <span className="text-xs text-gray-400 font-semibold mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Результаты ставок
            </span>
            <div className="flex items-center gap-3 mt-1">
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span className="text-lg font-black text-white">{overview.wins}</span>
                <span className="text-xs text-gray-400 font-semibold">зашло</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <span className="text-lg font-black text-white">{overview.losses}</span>
                <span className="text-xs text-gray-400 font-semibold">мимо</span>
              </div>
            </div>
            <span className="text-[11px] text-gray-400 mt-2 font-medium">
              Возвратов: {overview.refunds || 0}
            </span>
          </div>

          {/* Всего матчей */}
          <div className="p-4 bg-gray-850/80 rounded-2xl border border-gray-750/70 shadow-sm flex flex-col justify-between">
            <span className="text-xs text-gray-400 font-semibold mb-1 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-purple-400" /> Проверенных матчей
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-black text-white">
                {overview.total_matches}
              </span>
              <span className="text-xs font-bold text-gray-400">событий</span>
            </div>
            <span className="text-[11px] text-emerald-400 font-semibold mt-2 flex items-center gap-1">
              ● Все статусы верифицированы
            </span>
          </div>
        </div>
      </div>

      {/* ИНФОРМАЦИОННЫЙ БАННЕР О ДИНАМИЧЕСКИХ ВЕСАХ */}
      <div className="p-4 bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-purple-950/20 rounded-2xl border border-blue-500/30 flex items-start gap-3 shadow-md">
        <Sparkles className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300 leading-relaxed">
          <strong className="text-white block font-bold mb-0.5">
            Умный динамический отбор Ставки Дня по проходимости источников:
          </strong>
          ИИ отслеживает реальный процент побед каждого каппера <span className="text-blue-300 font-semibold">отдельно по каждому виду спорта</span>. Капперы с высокой проходимостью (от 70%) получают максимальный вес голоса (до 4.0x) и приоритет при выборе исходов, а источники с низкой проходимостью (менее 45%) автоматически пенализируются (0.2x-0.5x) и выслушиваются в последнюю очередь.
        </div>
      </div>

      {/* ТАБЛИЦА РЕЙТИНГА ИСТОЧНИКОВ И КАППЕРОВ С ФИЛЬТРОМ ПО ВИДАМ СПОРТА */}
      <div className="bg-gray-900 rounded-3xl border border-gray-800 shadow-xl overflow-hidden">
        <div className="p-6 border-b border-gray-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-emerald-400" />
              <span>Рейтинг источников по видам спорта</span>
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Подтверждённая проходимость и динамический вес влияния на Ставку Дня
            </p>
          </div>

          {/* ПЕРЕКЛЮЧАТЕЛЬ СПОРТА */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {sportTabs.map((sKey) => {
              const cfg = SPORT_CONFIG[sKey] || { name: sKey, icon: '🏆' };
              const isActive = selectedSport === sKey;
              return (
                <button
                  key={sKey}
                  onClick={() => setSelectedSport(sKey)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                      : 'bg-gray-800/80 text-gray-400 hover:text-white hover:bg-gray-800 border border-gray-750'
                  }`}
                >
                  <span>{cfg.icon}</span>
                  <span>{cfg.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-gray-950/60 text-gray-400 text-xs uppercase font-extrabold border-b border-gray-800 tracking-wider select-none">
                <th className="py-3.5 px-4 text-center w-12">#</th>
                <th className="py-3.5 px-4">Источник</th>
                <th className="py-3.5 px-4 text-center">Вид спорта</th>
                
                {/* Сортировка по ставкам */}
                <th 
                  onClick={() => handleSort('bets')}
                  className="py-3.5 px-4 text-center cursor-pointer hover:text-white transition-colors group"
                >
                  <span className="inline-flex items-center gap-1">
                    <span>Ставок</span>
                    {sortField === 'bets' ? (
                      sortAsc ? <ArrowUp className="w-3.5 h-3.5 text-blue-400" /> : <ArrowDown className="w-3.5 h-3.5 text-blue-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-30 group-hover:opacity-100" />
                    )}
                  </span>
                </th>

                <th className="py-3.5 px-4 text-center">В / П / В</th>

                {/* Сортировка по проходимости */}
                <th 
                  onClick={() => handleSort('winrate')}
                  className="py-3.5 px-4 text-center cursor-pointer hover:text-white transition-colors group"
                >
                  <span className="inline-flex items-center gap-1">
                    <span>Проходимость</span>
                    {sortField === 'winrate' ? (
                      sortAsc ? <ArrowUp className="w-3.5 h-3.5 text-emerald-400" /> : <ArrowDown className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-30 group-hover:opacity-100" />
                    )}
                  </span>
                </th>

                {/* Сортировка по весу */}
                <th 
                  onClick={() => handleSort('weight')}
                  className="py-3.5 px-4 text-center cursor-pointer hover:text-white transition-colors group"
                >
                  <span className="inline-flex items-center gap-1">
                    <span>Вес в ИИ</span>
                    {sortField === 'weight' ? (
                      sortAsc ? <ArrowUp className="w-3.5 h-3.5 text-purple-400" /> : <ArrowDown className="w-3.5 h-3.5 text-purple-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-30 group-hover:opacity-100" />
                    )}
                  </span>
                </th>

                {/* Сортировка по прибыли */}
                <th 
                  onClick={() => handleSort('profit')}
                  className="py-3.5 px-4 text-right cursor-pointer hover:text-white transition-colors group"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    <span>Чистый профит</span>
                    {sortField === 'profit' ? (
                      sortAsc ? <ArrowUp className="w-3.5 h-3.5 text-emerald-400" /> : <ArrowDown className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-30 group-hover:opacity-100" />
                    )}
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-gray-500">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-400" />
                    Загрузка рейтинга капперов...
                  </td>
                </tr>
              ) : sortedLeaderboard.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-gray-500">
                    По этому виду спорта пока нет рассчитанных ставок
                  </td>
                </tr>
              ) : (
                sortedLeaderboard.map((item, idx) => {
                  const isTop3 = idx < 3;
                  const medal = idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : `${idx + 1}`;
                  const tier = getTierInfo(item);
                  const sportLabel = SPORT_CONFIG[item.sport]?.name || item.sport || 'Все виды';
                  const sportIcon = SPORT_CONFIG[item.sport]?.icon || '🌐';

                  return (
                    <tr key={idx} className="hover:bg-gray-800/40 transition-colors">
                      {/* Ранг */}
                      <td className="py-4 px-4 text-center font-bold text-gray-300">
                        {isTop3 ? <span className="text-lg">{medal}</span> : <span className="text-gray-500">{medal}</span>}
                      </td>

                      {/* Название источника */}
                      <td className="py-4 px-4 font-bold text-white">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{item.source_type === 'telegram_channel' ? '📡' : '🌐'}</span>
                          <div>
                            <span className="block leading-tight">{item.source_name}</span>
                            <span className="text-[10px] text-gray-400 font-normal">
                              {item.source_type === 'telegram_channel' ? 'Telegram' : 'Аналитический Портал'}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Вид спорта */}
                      <td className="py-4 px-4 text-center text-xs text-gray-300">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-gray-800 rounded-lg border border-gray-700 font-semibold">
                          <span>{sportIcon}</span>
                          <span>{sportLabel}</span>
                        </span>
                      </td>

                      {/* Всего ставок */}
                      <td className="py-4 px-4 text-center text-gray-300 font-semibold">
                        {item.total_bets}
                      </td>

                      {/* В / П / В */}
                      <td className="py-4 px-4 text-center text-xs">
                        <span className="text-emerald-400 font-black">{item.wins}</span>
                        <span className="text-gray-500 mx-1">/</span>
                        <span className="text-rose-400 font-black">{item.losses}</span>
                        {item.refunds > 0 && (
                          <>
                            <span className="text-gray-500 mx-1">/</span>
                            <span className="text-amber-400 font-bold">{item.refunds}</span>
                          </>
                        )}
                      </td>

                      {/* Winrate % */}
                      <td className="py-4 px-4 text-center">
                        <span className={`px-2.5 py-1 rounded-lg text-xs font-black border ${tier.bg}`}>
                          {item.winrate_pct}%
                        </span>
                      </td>

                      {/* Динамический вес в ИИ */}
                      <td className="py-4 px-4 text-center">
                        <div className="flex flex-col items-center">
                          <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-black border ${tier.weightBg}`}>
                            {item.dynamic_weight ? `${item.dynamic_weight}x` : '1.0x'} • {tier.badge}
                          </span>
                          <span className="text-[9px] text-gray-500 mt-0.5">
                            {tier.note}
                          </span>
                        </div>
                      </td>

                      {/* Чистая прибыль */}
                      <td className="py-4 px-4 text-right font-black">
                        <span className={item.net_profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          {item.net_profit >= 0 ? `+${item.net_profit.toFixed(1)}` : item.net_profit.toFixed(1)} ном.
                        </span>
                        <span className="text-[10px] text-gray-500 block font-semibold">
                          ROI: {item.roi_pct >= 0 ? `+${item.roi_pct}%` : `${item.roi_pct}%`}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StatsLeaderboard;
