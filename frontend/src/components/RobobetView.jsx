import React, { useState, useEffect, useMemo } from 'react';
import { 
  Bot, Sparkles, RefreshCw, TrendingUp, AlertCircle, 
  ExternalLink, CheckCircle2, XCircle, Clock, Filter, ArrowUpRight,
  ShieldCheck, Zap, Award, Flame, Search, Trophy, Globe
} from 'lucide-react';
import { getRobobetPredictions, refreshRobobetPredictions } from '../api';
import TeamBadge from './TeamBadge';
import { getCountryDisplay } from './RobobetCard';
import RobobetMatchModal from './RobobetMatchModal';
import { toRussianTeam, toRussianLeague } from '../utils/russianNames';

// Helper to determine match outcome status (win/loss/refund/pending)
export const getOutcomeInfo = (m) => {
  if (!m) return { status: 'upcoming', label: 'ОЖИДАЕТСЯ', isWin: null, isFinished: false };

  // 1. If backend already evaluated result_status
  if (m.result_status === 'win' || m.is_win === true) {
    return { status: 'win', label: 'ПРОШЕЛ', isWin: true, isFinished: true };
  }
  if (m.result_status === 'loss' || m.is_win === false) {
    return { status: 'loss', label: 'НЕ ПРОШЕЛ', isWin: false, isFinished: true };
  }
  if (m.result_status === 'refund' || m.score === 'отм') {
    return { status: 'refund', label: 'ОТМЕНЕН', isWin: null, isFinished: true };
  }

  // 2. Client-side fallback check if score is available
  const scoreStr = (m.score || '').trim();
  if (scoreStr && scoreStr !== '- : -' && scoreStr.includes(':')) {
    const parts = scoreStr.split(':').map(s => parseInt(s.trim(), 10));
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
      const [h, a] = parts;
      const rec = (m.recommendation || '').toUpperCase().trim().replace('Х', 'X');
      let win = false;
      if (rec === 'П1' || rec === 'P1' || rec === '1') win = (h > a);
      else if (rec === 'П2' || rec === 'P2' || rec === '2') win = (a > h);
      else if (rec === 'X' || rec === 'НИЧЬЯ') win = (h === a);
      else if (rec === '1X') win = (h >= a);
      else if (rec === 'X2') win = (a >= h);
      else if (rec === '12') win = (h !== a);
      
      return {
        status: win ? 'win' : 'loss',
        label: win ? 'ПРОШЕЛ' : 'НЕ ПРОШЕЛ',
        isWin: win,
        isFinished: true
      };
    }
  }

  // 3. Если время матча наступило, но счёт ещё не зафиксирован — матч идёт в прямом эфире!
  if (m.match_status_label === 'live' || (m.is_time_past && !m.is_finished && (!m.score || m.score === '- : -'))) {
    return { status: 'live', label: 'В ИГРЕ', isWin: null, isFinished: false };
  }

  return { status: 'upcoming', label: 'ОЖИДАЕТСЯ', isWin: null, isFinished: false };
};

const RobobetView = ({ topBets = [] }) => {
  const [data, setData] = useState({ matches: [], bet_of_the_day: null, top_3_bets: [], total: 0, stats: null });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  
  // Filters: 'all', 'consensus', 'upcoming', 'won', 'lost', 'value', 'high_prob', 'p1', 'p2'
  const [filterType, setFilterType] = useState('all');
  const [selectedTournament, setSelectedTournament] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMatch, setSelectedMatch] = useState(null);

  const loadData = async (force = false) => {
    if (force) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const res = await getRobobetPredictions(force);
      setData(res);
    } catch (e) {
      setError("Не удалось загрузить данные Робобета.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const top3Bets = data.top_3_bets || [];
  const botd = data.bet_of_the_day;

  // Set of team names from topBets to highlight consensus
  const cappersMatchesMap = useMemo(() => {
    const map = new Map();
    for (const b of topBets) {
      const h = (b.home_team || '').toLowerCase().trim();
      const a = (b.away_team || '').toLowerCase().trim();
      if (h) map.set(h, b);
      if (a) map.set(a, b);
    }
    return map;
  }, [topBets]);

  // Summary statistics for today's matches
  const stats = useMemo(() => {
    const matches = data.matches || [];
    let wins = 0;
    let losses = 0;
    let refunds = 0;
    let finished = 0;
    let live = 0;
    let upcoming = 0;
    for (const m of matches) {
      const info = getOutcomeInfo(m);
      if (info.isFinished) {
        finished++;
        if (info.status === 'win') wins++;
        else if (info.status === 'loss') losses++;
        else if (info.status === 'refund') refunds++;
      } else if (info.status === 'live') {
        live++;
      } else {
        upcoming++;
      }
    }
    const decided = wins + losses;
    const winrate = decided > 0 ? Math.round((wins / decided) * 1000) / 10 : 0.0;
    return {
      total_matches: matches.length,
      finished,
      upcoming,
      live,
      wins,
      losses,
      refunds,
      winrate
    };
  }, [data]);

  const consensusCount = useMemo(() => {
    return (data.matches || []).filter(m => m.is_math_consensus).length;
  }, [data.matches]);

  // Список уникальных чемпионатов/стран с подсчетом матчей
  const availableTournaments = useMemo(() => {
    const counts = {};
    (data.matches || []).forEach(m => {
      const c = (m.country || 'Другие лиги').trim();
      counts[c] = (counts[c] || 0) + 1;
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [data.matches]);

  const filteredMatches = useMemo(() => {
    let list = data.matches || [];

    // 1. Фильтр по типу/статусу
    if (filterType === 'consensus') {
      list = list.filter(m => m.is_math_consensus);
    } else if (filterType === 'upcoming') {
      list = list.filter(m => !m.is_time_past && !getOutcomeInfo(m).isFinished && (!m.score || m.score === '- : -'));
    } else if (filterType === 'live') {
      list = list.filter(m => getOutcomeInfo(m).status === 'live');
    } else if (filterType === 'won') {
      list = list.filter(m => getOutcomeInfo(m).status === 'win');
    } else if (filterType === 'lost') {
      list = list.filter(m => getOutcomeInfo(m).status === 'loss');
    } else if (filterType === 'value') {
      list = list.filter(m => m.is_value);
    } else if (filterType === 'high_prob') {
      list = list.filter(m => m.rec_prob >= 65);
    } else if (filterType === 'p1') {
      list = list.filter(m => {
        const r = (m.recommendation || '').toUpperCase().trim();
        return r === 'П1' || r === '1' || r === 'P1';
      });
    } else if (filterType === 'p2') {
      list = list.filter(m => {
        const r = (m.recommendation || '').toUpperCase().trim();
        return r === 'П2' || r === '2' || r === 'P2';
      });
    } else if (filterType === 'dc') {
      list = list.filter(m => {
        const r = (m.recommendation || '').toUpperCase().trim();
        return r.includes('X') || r.includes('Х') || r === '12';
      });
    }

    // 2. Фильтр по турниру/чемпионату
    if (selectedTournament !== 'all') {
      list = list.filter(m => (m.country || '').trim() === selectedTournament);
    }

    // 3. Интеллектуальный двуязычный поиск (русский + оригинал + турнир)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(m => {
        const t1Ru = toRussianTeam(m.team1 || '').toLowerCase();
        const t2Ru = toRussianTeam(m.team2 || '').toLowerCase();
        const t1Orig = (m.team1 || '').toLowerCase();
        const t2Orig = (m.team2 || '').toLowerCase();
        const cRu = toRussianLeague(m.country || '').toLowerCase();
        const cOrig = (m.country || '').toLowerCase();
        const cDisp = getCountryDisplay(m.country || '').name.toLowerCase();
        
        return t1Ru.includes(q) || t2Ru.includes(q) ||
               t1Orig.includes(q) || t2Orig.includes(q) ||
               cRu.includes(q) || cOrig.includes(q) || cDisp.includes(q);
      });
    }

    return list;
  }, [data.matches, filterType, selectedTournament, searchQuery]);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Верхний баннер раздела */}
      <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-950/70 via-purple-950/50 to-gray-900 border border-purple-500/30 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2.5 mb-2 flex-wrap">
              <span className="px-3 py-1 rounded-full text-xs font-black bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1.5 shadow-sm">
                <Bot className="w-3.5 h-3.5 text-purple-400" />
                <span>МУЛЬТИ-ИИ СУПЕРКОМПЬЮТЕР</span>
              </span>
              <span className="text-xs font-bold text-gray-400">
                Тройной ИИ: Робобет (Poisson/EV) + Vitibet (Index/Score) + Zulubet (Math Tips)
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Раздел «Робобет & Тройной ИИ»: Без маржи БК
            </h2>
            <p className="text-xs sm:text-sm text-gray-300 mt-1.5 max-w-2xl leading-relaxed">
              Система объединяет математические модели 3 независимых алгоритмических платформ: <strong>Робобет</strong> (вероятности Пуассона и перевес +EV), <strong>Vitibet</strong> (индекс уверенности и точный счет) и <strong>Zulubet</strong> (алгоритмические вероятности). При полном согласии формируется максимальный рейтинг доверия (3/3).
            </p>
          </div>

          <button
            onClick={() => loadData(true)}
            disabled={refreshing || loading}
            className="self-start md:self-center flex items-center gap-2 px-5 py-3 rounded-2xl bg-purple-600/30 hover:bg-purple-600/40 border border-purple-500/40 text-purple-200 hover:text-white text-xs sm:text-sm font-black transition-all active:scale-95 disabled:opacity-50 shrink-0 shadow-lg"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Обновление...' : 'Обновить алгоритмы'}</span>
          </button>
        </div>

        {/* Сводный дашборд проходимости Робобета */}
        {stats.total_matches > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-5 border-t border-purple-500/20 relative z-10">
            <div className="bg-gray-950/60 p-3 rounded-2xl border border-gray-800/80">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Всего матчей в базе</div>
              <div className="text-xl font-black text-white font-mono mt-0.5">{stats.total_matches}</div>
            </div>
            <div className="bg-emerald-950/40 p-3 rounded-2xl border border-emerald-500/40">
              <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Прошло (Зашло)
              </div>
              <div className="text-xl font-black text-emerald-300 font-mono mt-0.5">{stats.wins}</div>
            </div>
            <div className="bg-rose-950/40 p-3 rounded-2xl border border-rose-500/40">
              <div className="text-[10px] font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1">
                <XCircle className="w-3 h-3 text-rose-400" /> Не зашло
              </div>
              <div className="text-xl font-black text-rose-300 font-mono mt-0.5">{stats.losses}</div>
            </div>
            <div className="bg-purple-950/50 p-3 rounded-2xl border border-purple-500/40">
              <div className="text-[10px] font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-purple-400" /> Проходимость Робобета
              </div>
              <div className="text-xl font-black text-purple-200 font-mono mt-0.5">
                {stats.winrate}% {stats.finished > 0 && <span className="text-xs font-semibold text-gray-400">({stats.finished} завершено)</span>}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ПОДИУМ: ТОП-3 МАТЕМАТИЧЕСКИХ СТАВКИ ДНЯ */}
      {top3Bets.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-lg shadow-md shadow-amber-500/10">
                🏆
              </div>
              <div>
                <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2 flex-wrap">
                  <span>ТОП-3 Математических Ставки Дня</span>
                  <span className="text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-gradient-to-r from-amber-500/20 to-purple-500/20 text-amber-300 border border-amber-400/30">
                    Консенсус ИИ
                  </span>
                  <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Кэф ≥ 1.55
                  </span>
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Три наилучших профитных матча с кэфом от 1.55, высокой проходимостью и взаимным подтверждением моделей
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {top3Bets.map((bet, idx) => {
              const outcome = getOutcomeInfo(bet);
              const isGold = idx === 0;
              const isSilver = idx === 1;
              const isBronze = idx === 2;

              let cardBg = 'bg-gradient-to-b from-gray-900 via-gray-950 to-gray-950 border-gray-800';
              let badgeColor = 'bg-gray-800 text-gray-200 border-gray-700';
              let medalIcon = '🥇';
              let rankTitle = '1-Е МЕСТО • ГЛАВНАЯ СТАВКА';

              if (isGold) {
                cardBg = 'bg-gradient-to-b from-amber-950/40 via-purple-950/20 to-gray-950 border-amber-500/50 shadow-amber-500/10';
                badgeColor = 'bg-amber-500/20 text-amber-300 border-amber-500/40';
                medalIcon = '🥇';
                rankTitle = 'ТОП 1 • ЗОЛОТОЙ ВЫБОР';
              } else if (isSilver) {
                cardBg = 'bg-gradient-to-b from-slate-900/60 via-purple-950/20 to-gray-950 border-slate-400/40 shadow-slate-400/5';
                badgeColor = 'bg-slate-500/20 text-slate-200 border-slate-400/40';
                medalIcon = '🥈';
                rankTitle = 'ТОП 2 • СЕРЕБРЯНЫЙ ВЫБОР';
              } else if (isBronze) {
                cardBg = 'bg-gradient-to-b from-orange-950/40 via-purple-950/20 to-gray-950 border-orange-500/40 shadow-orange-500/5';
                badgeColor = 'bg-orange-500/20 text-orange-300 border-orange-500/40';
                medalIcon = '🥉';
                rankTitle = 'ТОП 3 • БРОНЗОВЫЙ ВЫБОР';
              }

              return (
                <div 
                  key={bet.id || idx}
                  onClick={() => setSelectedMatch(bet)}
                  className={`p-5 rounded-3xl border-2 shadow-xl hover:-translate-y-1 cursor-pointer transition-all flex flex-col justify-between gap-4 relative overflow-hidden group ${cardBg}`}
                >
                  {/* Медаль и Шапка */}
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black border shadow-sm ${badgeColor}`}>
                        <span>{medalIcon}</span>
                        <span>{rankTitle}</span>
                      </span>

                      {outcome.status === 'win' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/50">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>ЗАШЕЛ ({bet.score})</span>
                        </span>
                      ) : outcome.status === 'loss' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-500/20 text-rose-300 border border-rose-500/50">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>НЕ ЗАШЕЛ ({bet.score})</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-gray-950/80 text-gray-300 text-xs font-mono font-bold border border-gray-800">
                          <Clock className="w-3 h-3 text-purple-400" />
                          <span>{bet.time}</span>
                        </span>
                      )}
                    </div>

                    {/* Противостояние команд с эмблемами */}
                    <div className="flex items-center justify-between gap-2 p-2.5 rounded-2xl bg-gray-950/60 border border-gray-800/80 my-2">
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <TeamBadge teamName={bet.team1} logoUrl={bet.home_logo} size="sm" />
                        <span className="text-xs font-black text-white truncate" title={bet.team1}>{bet.team1}</span>
                      </div>
                      <span className="text-[10px] font-black text-purple-400 font-mono px-1">VS</span>
                      <div className="flex items-center gap-2 min-w-0 flex-1 justify-end text-right">
                        <span className="text-xs font-black text-white truncate" title={bet.team2}>{bet.team2}</span>
                        <TeamBadge teamName={bet.team2} logoUrl={bet.away_logo} size="sm" />
                      </div>
                    </div>

                    {bet.country && (() => {
                      const cDisplay = getCountryDisplay(bet.country, bet.country_flag_url, bet.country_emoji);
                      return (
                        <div className="text-[11px] font-semibold text-gray-400 mt-1 flex items-center gap-1.5" title={cDisplay.name}>
                          {cDisplay.flag ? (
                            <img 
                              src={cDisplay.flag} 
                              alt="" 
                              className="w-3.5 h-2.5 object-cover rounded-[2px] opacity-80 shrink-0" 
                              onError={(e) => { e.currentTarget.style.display = 'none'; }}
                            />
                          ) : (
                            <span>{cDisplay.emoji}</span>
                          )}
                          <span>{cDisplay.name}</span>
                          {bet.is_value && (
                            <span className="text-emerald-400 font-black font-mono ml-2">
                              +EV {Math.round(bet.ev * 100)}%
                            </span>
                          )}
                        </div>
                      );
                    })()}

                    {/* Шкала вероятностей */}
                    <div className="mt-3 bg-gray-950/50 p-2 rounded-xl border border-gray-800/80">
                      <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 mb-1">
                        <span className="text-emerald-400">1: {bet.prob_1}%</span>
                        <span className="text-amber-400">X: {bet.prob_x}%</span>
                        <span className="text-blue-400">2: {bet.prob_2}%</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-gray-800 overflow-hidden flex">
                        <div style={{ width: `${bet.prob_1}%` }} className="bg-emerald-500 h-full"></div>
                        <div style={{ width: `${bet.prob_x}%` }} className="bg-amber-500 h-full"></div>
                        <div style={{ width: `${bet.prob_2}%` }} className="bg-blue-500 h-full"></div>
                      </div>
                    </div>
                  </div>

                  {/* БЛОК МУЛЬТИ-ИИ ПОДТВЕРЖДЕНИЯ (Робобет + Vitibet + Zulubet) */}
                  <div className="space-y-2 pt-2 border-t border-gray-800/80">
                    {bet.is_triple_consensus ? (
                      <div className="p-2 rounded-xl bg-gradient-to-r from-rose-500/20 via-amber-500/20 to-transparent border border-rose-500/40 flex items-center justify-between">
                        <span className="text-[11px] font-black text-rose-300 flex items-center gap-1.5 animate-pulse">
                          <Flame className="w-3.5 h-3.5 text-rose-400" />
                          <span>🔥 СУПЕР ИИ 3/3 (Triple AI)</span>
                        </span>
                        <span className="text-[10px] font-bold text-amber-200">
                          Робобет + Vitibet + Zulubet
                        </span>
                      </div>
                    ) : bet.is_math_consensus ? (
                      <div className="p-2 rounded-xl bg-gradient-to-r from-amber-500/15 via-purple-500/15 to-transparent border border-amber-500/30 flex items-center justify-between">
                        <span className="text-[11px] font-black text-amber-300 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                          <span>Консенсус 2-х ИИ</span>
                        </span>
                        <span className="text-[10px] font-bold text-purple-200">
                          {bet.has_vitibet && bet.has_zulubet ? 'Два алгоритма' : 'Робобет + Модель'}
                        </span>
                      </div>
                    ) : null}

                    <div className="grid grid-cols-3 gap-1.5 text-xs">
                      <div className="p-2 rounded-xl bg-gray-950/60 border border-gray-800 text-center">
                        <div className="text-[9px] text-gray-400 uppercase font-bold">Робобет</div>
                        <div className="text-xs sm:text-sm font-black text-emerald-400 font-mono mt-0.5">
                          {bet.rec_prob}%
                        </div>
                      </div>

                      <div className="p-2 rounded-xl bg-gray-950/60 border border-gray-800 text-center">
                        <div className="text-[9px] text-gray-400 uppercase font-bold">Vitibet</div>
                        <div className="text-xs sm:text-sm font-black text-blue-300 font-mono mt-0.5">
                          {bet.vitibet_proj_score || '—'}
                        </div>
                      </div>

                      <div className="p-2 rounded-xl bg-gray-950/60 border border-gray-800 text-center">
                        <div className="text-[9px] text-gray-400 uppercase font-bold">Zulubet</div>
                        <div className="text-xs sm:text-sm font-black text-cyan-300 font-mono mt-0.5" title={bet.has_zulubet ? `1: ${bet.zulubet_prob_1}% | X: ${bet.zulubet_prob_x}% | 2: ${bet.zulubet_prob_2}%` : ''}>
                          {bet.has_zulubet ? bet.zulubet_tip : '—'}
                        </div>
                      </div>
                    </div>

                    {/* Прогноз и Кэф */}
                    <div className="p-3 rounded-2xl bg-purple-950/30 border border-purple-500/30 flex items-center justify-between">
                      <div>
                        <div className="text-[10px] uppercase font-bold text-gray-400">Рекомендация</div>
                        <div className="text-lg font-black text-amber-300 font-mono">
                          {bet.recommendation}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] uppercase font-bold text-gray-400">Кэф БК</div>
                        <div className="text-lg font-black text-white font-mono">
                          {bet.rec_odd ? Number(bet.rec_odd).toFixed(2) : '-'}
                        </div>
                      </div>
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Панель фильтров матчей Робобета */}
      <div className="space-y-3 pt-4 border-t border-gray-800">
        {/* Верхняя строка: Тип фильтра + Поиск по командам */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-gray-400 flex items-center gap-1.5 mr-1">
              <Filter className="w-3.5 h-3.5 text-gray-400" />
              <span>Фильтр:</span>
            </span>

            {[
              { id: 'all', label: `Все (${data.matches?.length || 0})` },
              { id: 'consensus', label: `🔥 Консенсус ИИ (${consensusCount})` },
              { id: 'upcoming', label: `Не начались (${stats.upcoming})` },
              { id: 'live', label: `🔴 В игре (${stats.live || 0})` },
              { id: 'won', label: `✅ Прошли (${stats.wins})` },
              { id: 'lost', label: `❌ Не зашли (${stats.losses})` },
              { id: 'high_prob', label: 'Проходимость >65%' },
              { id: 'value', label: 'Валуйные (+EV)' },
              { id: 'p1', label: 'П1' },
              { id: 'p2', label: 'П2' },
              { id: 'dc', label: '1X / X2 (Двойной шанс)' },
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilterType(f.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  filterType === f.id
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30 scale-[1.02]'
                    : 'bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Быстрый поиск по названию команды */}
          <div className="relative min-w-[200px] max-w-xs flex-1">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Поиск команды..."
              className="w-full bg-gray-950/90 border border-gray-800 rounded-xl pl-8 pr-7 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white text-xs"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Вторая строка: Селектор турниров и лиг (Лига Европы, Англия, Испания и т.д.) */}
        {availableTournaments.length > 1 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 no-scrollbar">
            <span className="text-xs font-bold text-gray-400 flex items-center gap-1.5 shrink-0 mr-1">
              <Trophy className="w-3.5 h-3.5 text-amber-400" />
              <span>Турнир:</span>
            </span>

            <button
              onClick={() => setSelectedTournament('all')}
              className={`px-3 py-1 rounded-xl text-xs font-bold whitespace-nowrap transition-all shrink-0 ${
                selectedTournament === 'all'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm'
                  : 'bg-gray-900/80 hover:bg-gray-800 text-gray-400 border border-gray-800'
              }`}
            >
              🏆 Все лиги ({data.matches?.length || 0})
            </button>

            {availableTournaments.map(([tName, count]) => {
              const cDisplay = getCountryDisplay(tName);
              const isSelected = selectedTournament === tName;
              return (
                <button
                  key={tName}
                  onClick={() => setSelectedTournament(isSelected ? 'all' : tName)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold whitespace-nowrap transition-all shrink-0 flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-purple-600/30 text-purple-200 border border-purple-500 shadow-sm shadow-purple-600/20'
                      : 'bg-gray-900/80 hover:bg-gray-800 text-gray-300 border border-gray-800'
                  }`}
                >
                  {cDisplay.flag ? (
                    <img 
                      src={cDisplay.flag} 
                      alt="" 
                      className="w-3.5 h-2.5 object-cover rounded-[1px] opacity-90 shrink-0" 
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  ) : (
                    <span>{cDisplay.emoji}</span>
                  )}
                  <span>{cDisplay.name}</span>
                  <span className="text-[10px] text-gray-500 font-mono ml-0.5">({count})</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Индикатор количества и сброса фильтра */}
        <div className="flex items-center justify-between text-xs font-bold text-gray-400 pt-1">
          <div>
            Показано: <span className="text-white font-mono font-black">{filteredMatches.length}</span> матчей
            {selectedTournament !== 'all' && (
              <span className="text-purple-300 ml-2 font-normal">
                (в лиге: <strong>{getCountryDisplay(selectedTournament).name}</strong>)
              </span>
            )}
            {searchQuery && (
              <span className="text-amber-300 ml-2 font-normal">
                (поиск: <strong>«{searchQuery}»</strong>)
              </span>
            )}
          </div>
          {(selectedTournament !== 'all' || filterType !== 'all' || searchQuery) && (
            <button
              onClick={() => {
                setSelectedTournament('all');
                setFilterType('all');
                setSearchQuery('');
              }}
              className="text-purple-400 hover:text-purple-300 underline font-normal"
            >
              Сбросить фильтры
            </button>
          )}
        </div>
      </div>

      {/* Список всех матчей Робобета */}
      {loading ? (
        <div className="py-16 text-center text-gray-400">
          <Bot className="w-8 h-8 mx-auto text-purple-400 animate-bounce mb-3" />
          <p className="text-sm font-bold">Синхронизируем расчеты математических суперкомпьютеров...</p>
        </div>
      ) : filteredMatches.length === 0 ? (
        <div className="py-12 text-center text-gray-500 bg-gray-900/50 rounded-2xl border border-gray-800">
          <p className="text-sm font-semibold">По выбранному фильтру матчей не найдено.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMatches.map(m => {
            const outcome = getOutcomeInfo(m);
            const hasCapperConsensus = cappersMatchesMap.has((m.team1 || '').toLowerCase().trim()) || 
                                       cappersMatchesMap.has((m.team2 || '').toLowerCase().trim());

            // Border and background highlighting based on outcome status
            let cardClasses = 'bg-gray-900/90 border-gray-800 hover:border-purple-500/40';
            if (outcome.status === 'win') {
              cardClasses = 'bg-gradient-to-b from-gray-900 via-gray-900 to-emerald-950/20 border-emerald-500/40 hover:border-emerald-400 shadow-emerald-500/5';
            } else if (outcome.status === 'loss') {
              cardClasses = 'bg-gradient-to-b from-gray-900 via-gray-900 to-rose-950/20 border-rose-500/30 hover:border-rose-400/50 shadow-rose-500/5';
            }

            return (
              <div 
                key={m.id}
                onClick={() => setSelectedMatch(m)}
                className={`p-4 sm:p-5 rounded-2xl border transition-all shadow-md flex flex-col justify-between gap-3 group relative overflow-hidden cursor-pointer hover:-translate-y-0.5 hover:shadow-xl hover:border-purple-500/50 ${cardClasses}`}
              >
                <div>
                  {/* Верхняя строка: Время, страна, счет, результат */}
                  <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-gray-300 bg-gray-800 px-2 py-0.5 rounded">
                        {m.time}
                      </span>
                      {m.country && (() => {
                        const cDisplay = getCountryDisplay(m.country, m.country_flag_url, m.country_emoji);
                        return (
                          <span className="text-[10px] font-bold text-gray-300 bg-gray-800/80 px-2 py-0.5 rounded inline-flex items-center gap-1" title={cDisplay.name}>
                            {cDisplay.flag ? (
                              <img 
                                src={cDisplay.flag} 
                                alt="" 
                                className="w-3 h-2 object-cover rounded-[1px] opacity-80 shrink-0" 
                                onError={(e) => { e.currentTarget.style.display = 'none'; }}
                              />
                            ) : (
                              <span>{cDisplay.emoji}</span>
                            )}
                            <span>{cDisplay.name}</span>
                          </span>
                        );
                      })()}

                      {/* СЧЕТ МАТЧА */}
                      {m.score && m.score !== '- : -' && (
                        <span className={`text-xs font-mono font-black px-2.5 py-0.5 rounded border shadow-inner ${
                          outcome.status === 'win'
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-500/60'
                            : outcome.status === 'loss'
                              ? 'bg-rose-950 text-rose-300 border-rose-500/60'
                              : 'bg-gray-800 text-gray-200 border-gray-700'
                        }`}>
                          {m.score}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* ЧЕТКИЙ ИНДИКАТОР ПРОХОДИМОСТИ: ПРОШЕЛ / НЕ ПРОШЕЛ / В ИГРЕ */}
                      {outcome.status === 'live' && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-black bg-rose-500/20 text-rose-300 border border-rose-500/50 animate-pulse">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                          <span>В ИГРЕ</span>
                        </span>
                      )}
                      {outcome.status === 'win' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>ПРОШЕЛ</span>
                        </span>
                      )}
                      {outcome.status === 'loss' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-black bg-rose-500/20 text-rose-300 border border-rose-500/50 shadow-sm shadow-rose-500/20">
                          <XCircle className="w-3.5 h-3.5 text-rose-400" />
                          <span>НЕ ПРОШЕЛ</span>
                        </span>
                      )}
                      {outcome.status === 'refund' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-black bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          ОТМЕНЕН
                        </span>
                      )}

                      {hasCapperConsensus && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 shadow-sm">
                          <Sparkles className="w-3 h-3 text-amber-400" />
                          <span>ИИ + Капперы</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Названия команд с эмблемами */}
                  <div className="flex items-center gap-2.5 my-2">
                    <TeamBadge teamName={toRussianTeam(m.team1)} logoUrl={m.home_logo} size="sm" />
                    <div className="text-sm sm:text-base font-black text-white group-hover:text-purple-300 transition-colors flex-1 min-w-0 truncate font-heading">
                      {toRussianTeam(m.team1)} <span className="text-purple-400 font-bold mx-1">vs</span> {toRussianTeam(m.team2)}
                    </div>
                    <TeamBadge teamName={toRussianTeam(m.team2)} logoUrl={m.away_logo} size="sm" />
                  </div>

                  {/* ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ ВИТИБЕТ, ZULUBET И КОНСЕНСУС */}
                  <div className="flex items-center gap-1.5 flex-wrap mt-1.5">
                    {m.is_triple_consensus ? (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-gradient-to-r from-rose-500/25 to-amber-500/25 text-rose-300 border border-rose-500/50 flex items-center gap-1 shadow-sm animate-pulse">
                        <Flame className="w-3 h-3 text-rose-400" />
                        <span>🔥 СУПЕР ИИ 3/3</span>
                      </span>
                    ) : m.is_math_consensus ? (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 shadow-sm">
                        <Sparkles className="w-3 h-3 text-amber-400" />
                        <span>Консенсус 2-х ИИ</span>
                      </span>
                    ) : null}

                    {m.vitibet_proj_score && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-950/70 text-blue-300 border border-blue-800/60 font-mono">
                        🎯 Счёт Vitibet: {m.vitibet_proj_score}
                      </span>
                    )}

                    {m.has_zulubet && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-cyan-950/70 text-cyan-300 border border-cyan-800/60 font-mono" title={`Zulubet: 1(${m.zulubet_prob_1}%) X(${m.zulubet_prob_x}%) 2(${m.zulubet_prob_2}%)`}>
                        🤖 Zulu: {m.zulubet_tip}
                      </span>
                    )}

                    {m.vitibet_index && (
                      <span className="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-gray-800/80 text-gray-300 border border-gray-700/60 font-mono">
                        Инд: {m.vitibet_index}
                      </span>
                    )}
                  </div>
                </div>

                {/* Шкала распределения вероятностей (П1, X, П2) */}
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center justify-between text-[11px] font-bold text-gray-400">
                    <span className="text-emerald-400">1: {m.prob_1}%</span>
                    <span className="text-amber-400">X: {m.prob_x}%</span>
                    <span className="text-blue-400">2: {m.prob_2}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-gray-800 overflow-hidden flex">
                    <div style={{ width: `${m.prob_1}%` }} className="bg-emerald-500 h-full"></div>
                    <div style={{ width: `${m.prob_x}%` }} className="bg-amber-500 h-full"></div>
                    <div style={{ width: `${m.prob_2}%` }} className="bg-blue-500 h-full"></div>
                  </div>
                </div>

                {/* Нижняя плашка: Рекомендация и Кэф со статусом захода */}
                <div className="pt-2 border-t border-gray-800/80 flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 font-bold">Прогноз:</span>
                    <span className={`px-2.5 py-0.5 rounded-lg text-xs font-black border transition-all ${
                      outcome.status === 'win'
                        ? 'bg-emerald-500/20 text-emerald-200 border-emerald-500/50 shadow-sm shadow-emerald-500/20'
                        : outcome.status === 'loss'
                          ? 'bg-rose-950/60 text-rose-300 border-rose-600/40 line-through'
                          : 'bg-purple-600/30 text-purple-200 border border-purple-500/40'
                    }`}>
                      {m.recommendation}
                    </span>
                    <span className="text-xs font-bold text-gray-300 font-mono">
                      кэф {m.rec_odd ? Number(m.rec_odd).toFixed(2) : '-'}
                    </span>

                    {outcome.status === 'win' && (
                      <span className="text-[11px] font-black text-emerald-400 font-mono ml-1">
                        +{(Number(m.rec_odd) - 1).toFixed(2)}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    {m.is_value && (
                      <span className="text-emerald-400 font-bold font-mono">
                        +EV {Math.round(m.ev * 100)}%
                      </span>
                    )}
                    {m.match_url && (
                      <a
                        href={m.match_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-400 hover:text-white p-1"
                        title="Ссылка на источник"
                      >
                        <ArrowUpRight className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Модальное окно углубленного анализа матча Робобета */}
      {selectedMatch && (
        <RobobetMatchModal 
          match={selectedMatch} 
          onClose={() => setSelectedMatch(null)} 
        />
      )}
    </div>
  );
};

export default RobobetView;
