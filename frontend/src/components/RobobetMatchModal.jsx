import React from 'react';
import { 
  X, Bot, Sparkles, Flame, Clock, ExternalLink, 
  CheckCircle2, XCircle, TrendingUp, ShieldCheck, Zap 
} from 'lucide-react';
import TeamBadge from './TeamBadge';
import { getCountryDisplay } from './RobobetCard';
import { getOutcomeInfo } from './RobobetView';
import { toRussianTeam, toRussianLeague } from '../utils/russianNames';

const RobobetMatchModal = ({ match, onClose }) => {
  if (!match) return null;

  const team1 = toRussianTeam(match.team1);
  const team2 = toRussianTeam(match.team2);
  const tournamentName = toRussianLeague(match.country);

  const outcome = getOutcomeInfo(match);
  const cDisplay = getCountryDisplay(match.country, match.country_flag_url, match.country_emoji);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div 
        className="relative w-full max-w-2xl bg-gradient-to-b from-gray-900 via-gray-950 to-gray-950 rounded-3xl border border-purple-500/40 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Заголовок модалки */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-gray-800 bg-gray-900/60">
          <div className="flex items-center gap-2.5">
            <span className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300">
              <Bot className="w-4 h-4" />
            </span>
            <div>
              <div className="text-[10px] font-black uppercase tracking-wider text-purple-300 font-heading">
                Математический AI-Анализ
              </div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                <span>{tournamentName}</span>
                {cDisplay.flag && (
                  <img src={cDisplay.flag} alt="" className="w-4 h-3 object-cover rounded-[2px]" />
                )}
              </div>
            </div>
          </div>

          <button 
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Тело модалки со скроллом */}
        <div className="p-4 sm:p-6 overflow-y-auto space-y-5 custom-scrollbar">
          {/* Статус и Время */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-xl bg-gray-800/80 border border-gray-700 text-xs font-bold text-gray-200 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-purple-400" />
                <span>{match.time ? `${match.time} МСК` : 'Сегодня'}</span>
              </span>

              {match.score && match.score !== '- : -' && (
                <span className={`px-3 py-1 rounded-xl text-xs font-black font-mono border ${
                  outcome.status === 'win' 
                    ? 'bg-emerald-950 text-emerald-300 border-emerald-500/60' 
                    : outcome.status === 'loss'
                      ? 'bg-rose-950 text-rose-300 border-rose-500/60'
                      : 'bg-gray-800 text-gray-200 border-gray-700'
                }`}>
                  Счет: {match.score}
                </span>
              )}
            </div>

            {/* Бейдж исхода */}
            {outcome.status === 'win' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>ПРОШЕЛ</span>
              </span>
            )}
            {outcome.status === 'loss' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-rose-500/20 text-rose-300 border border-rose-500/50 shadow-sm shadow-rose-500/20">
                <XCircle className="w-4 h-4 text-rose-400" />
                <span>НЕ ПРОШЕЛ</span>
              </span>
            )}
            {outcome.status === 'live' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-rose-500/20 text-rose-300 border border-rose-500/50 animate-pulse">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                <span>МАТЧ В ИГРЕ</span>
              </span>
            )}
            {outcome.status === 'upcoming' && (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-gray-800 text-gray-300 border border-gray-700">
                ОЖИДАЕТСЯ
              </span>
            )}
          </div>

          {/* Карточка матча (Хозяева vs Гости) с большими эмблемами */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 p-4 bg-gray-950/70 rounded-3xl border border-gray-800/80">
            <div className="flex flex-col items-center text-center">
              <TeamBadge teamName={team1} logoUrl={match.home_logo} size="xl" className="mb-2.5 !w-20 !h-20" />
              <span className="text-base sm:text-xl font-black text-white leading-tight line-clamp-2 font-heading tracking-tight drop-shadow-sm">
                {team1}
              </span>
              <span className="text-[11px] text-gray-400 font-bold mt-1 uppercase tracking-wider">Хозяева</span>
            </div>

            <div className="flex flex-col items-center justify-center px-2">
              <span className="w-10 h-10 rounded-full bg-purple-950 border border-purple-700/60 flex items-center justify-center text-xs font-black text-purple-300 italic shadow-inner font-heading">
                VS
              </span>
            </div>

            <div className="flex flex-col items-center text-center">
              <TeamBadge teamName={team2} logoUrl={match.away_logo} size="xl" className="mb-2.5 !w-20 !h-20" />
              <span className="text-base sm:text-xl font-black text-white leading-tight line-clamp-2 font-heading tracking-tight drop-shadow-sm">
                {team2}
              </span>
              <span className="text-[11px] text-gray-400 font-bold mt-1 uppercase tracking-wider">Гости</span>
            </div>
          </div>

          {/* Плашка консенсуса, если есть */}
          {match.is_triple_consensus ? (
            <div className="p-3 rounded-2xl bg-gradient-to-r from-rose-500/20 via-amber-500/20 to-purple-500/10 border border-rose-500/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-rose-400 animate-pulse" />
                <div>
                  <div className="text-xs font-black text-rose-300">🔥 СУПЕР ИИ 3/3 (Triple AI Consensus)</div>
                  <div className="text-[11px] text-rose-200/80">Робобет, Vitibet и Zulubet полностью сошлись в одном прогнозе</div>
                </div>
              </div>
            </div>
          ) : match.is_math_consensus ? (
            <div className="p-3 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <div className="text-xs font-bold text-amber-200">
                Консенсус 2-х алгоритмов подтверждает перевес
              </div>
            </div>
          ) : null}

          {/* Рекомендация и коэффициент */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-3 rounded-2xl bg-purple-950/40 border border-purple-500/30 text-center">
              <div className="text-[10px] text-gray-400 font-bold uppercase">Рекомендация</div>
              <div className="text-xl font-black text-amber-300 font-mono mt-0.5">
                {match.recommendation || '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-gray-950/60 border border-gray-800 text-center">
              <div className="text-[10px] text-gray-400 font-bold uppercase">Кэф букмекера</div>
              <div className="text-xl font-black text-white font-mono mt-0.5">
                {match.rec_odd ? Number(match.rec_odd).toFixed(2) : '-'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-gray-950/60 border border-gray-800 text-center">
              <div className="text-[10px] text-gray-400 font-bold uppercase">Вероятность ИИ</div>
              <div className="text-xl font-black text-emerald-400 font-mono mt-0.5">
                {match.rec_prob}%
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-gray-950/60 border border-gray-800 text-center">
              <div className="text-[10px] text-gray-400 font-bold uppercase">Мат. ожидание</div>
              <div className={`text-xl font-black font-mono mt-0.5 ${match.is_value ? 'text-emerald-400' : 'text-gray-300'}`}>
                {match.ev > 0 ? `+${Math.round(match.ev * 100)}%` : `${Math.round(match.ev * 100)}%`}
              </div>
            </div>
          </div>

          {/* Матрица 3-х систем искусственного интеллекта */}
          <div className="bg-gray-950/80 rounded-2xl border border-gray-800 p-4 space-y-3">
            <div className="text-xs font-black uppercase tracking-wider text-purple-300 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              <span>Сравнение независимых моделей анализа</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {/* Робобет */}
              <div className="p-3 rounded-xl bg-gray-900/80 border border-gray-800">
                <div className="text-[11px] font-bold text-emerald-400 mb-1">🤖 1. Робобет (Пуассон)</div>
                <div className="text-xs text-gray-300 space-y-1">
                  <div>П1: <span className="font-mono font-bold text-white">{match.prob_1}%</span></div>
                  <div>Ничья: <span className="font-mono font-bold text-white">{match.prob_x}%</span></div>
                  <div>П2: <span className="font-mono font-bold text-white">{match.prob_2}%</span></div>
                </div>
              </div>

              {/* Vitibet */}
              <div className="p-3 rounded-xl bg-gray-900/80 border border-gray-800">
                <div className="text-[11px] font-bold text-blue-400 mb-1">🎯 2. Vitibet Engine</div>
                <div className="text-xs text-gray-300 space-y-1">
                  <div>Счет: <span className="font-mono font-bold text-white">{match.vitibet_proj_score || '—'}</span></div>
                  <div>Исход: <span className="font-mono font-bold text-white">{match.vitibet_tip || '—'}</span></div>
                  <div>Индекс: <span className="font-mono font-bold text-white">{match.vitibet_index || '—'}</span></div>
                </div>
              </div>

              {/* Zulubet */}
              <div className="p-3 rounded-xl bg-gray-900/80 border border-gray-800">
                <div className="text-[11px] font-bold text-cyan-400 mb-1">⚡ 3. Zulubet Math</div>
                <div className="text-xs text-gray-300 space-y-1">
                  <div>Совет: <span className="font-mono font-bold text-white">{match.zulubet_tip || '—'}</span></div>
                  <div>1X2: <span className="font-mono font-bold text-white">
                    {match.has_zulubet ? `${match.zulubet_prob_1}% / ${match.zulubet_prob_x}% / ${match.zulubet_prob_2}%` : '—'}
                  </span></div>
                </div>
              </div>
            </div>
          </div>

          {/* Ссылка на источник / трансляцию */}
          {match.match_url && (
            <div className="pt-2">
              <a 
                href={match.match_url} 
                target="_blank" 
                rel="noreferrer noopener"
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/40 text-purple-200 hover:text-white text-xs font-black transition-all shadow-lg active:scale-[0.98]"
              >
                <span>Открыть трансляцию и матч-центр матча</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RobobetMatchModal;
