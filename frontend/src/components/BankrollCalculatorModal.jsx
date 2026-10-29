import React, { useState } from 'react';
import { Calculator, X, DollarSign, TrendingUp, ShieldCheck, Zap, Sparkles, ArrowRight } from 'lucide-react';

export default function BankrollCalculatorModal({ isOpen, onClose, currentWinrate = 82.6, currentFlatProfit = 18.58 }) {
  const [bankroll, setBankroll] = useState(10000);
  const [flatPercent, setFlatPercent] = useState(3);
  const [customOdds, setCustomOdds] = useState(1.85);

  if (!isOpen) return null;

  const oneFlatAmount = Math.round((bankroll * flatPercent) / 100);
  const potentialNetProfitPerBet = Math.round(oneFlatAmount * (customOdds - 1));
  const estimatedMonthProfit = Math.round(oneFlatAmount * currentFlatProfit);
  const totalProjectedBank = bankroll + estimatedMonthProfit;
  const growthPercent = ((estimatedMonthProfit / bankroll) * 100).toFixed(1);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div 
        className="relative w-full max-w-lg bg-[#0e1626] border border-cyan-500/30 rounded-3xl p-6 sm:p-7 shadow-2xl shadow-cyan-950/40 text-white overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Glow ambient */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>

        {/* Header */}
        <div className="flex items-center justify-between gap-4 pb-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-2xl shadow-lg shadow-cyan-500/20">
              <Calculator className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-black text-white font-heading flex items-center gap-2">
                <span>Калькулятор Флэта & Банка</span>
                <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Инновация
                </span>
              </h3>
              <p className="text-xs text-gray-400">
                Финансовый расчет прибыли по алгоритмам ИИ
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Controls */}
        <div className="space-y-4 my-5">
          {/* Bankroll input */}
          <div>
            <label className="text-xs font-bold text-gray-300 uppercase tracking-wider block mb-1.5">
              Ваш общий банк:
            </label>
            <div className="relative">
              <input 
                type="number" 
                value={bankroll}
                onChange={(e) => setBankroll(Math.max(100, Number(e.target.value) || 0))}
                className="w-full bg-[#0a0f1d] border border-gray-700 rounded-xl px-4 py-3 text-base font-black text-white focus:outline-none focus:border-cyan-400 transition-colors"
                step={500}
              />
              <span className="absolute right-4 top-3.5 text-xs font-bold text-cyan-400">
                ₽ РУБ
              </span>
            </div>
            <div className="flex gap-2 mt-2">
              {[5000, 10000, 25000, 50000, 100000].map((preset) => (
                <button
                  key={preset}
                  onClick={() => setBankroll(preset)}
                  className={`text-[11px] font-bold px-2 py-1 rounded-lg border transition-all ${
                    bankroll === preset 
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400/40' 
                      : 'bg-white/[0.03] text-gray-400 border-white/[0.06] hover:text-white'
                  }`}
                >
                  {(preset / 1000).toFixed(0)}k
                </button>
              ))}
            </div>
          </div>

          {/* Flat Size Selector */}
          <div>
            <label className="text-xs font-bold text-gray-300 uppercase tracking-wider block mb-1.5">
              Размер 1 флэта (% от банка):
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { percent: 1, label: '1% (Консервативный)', desc: 'Минимум риска' },
                { percent: 3, label: '3% (Сбалансированный)', desc: 'Оптимально' },
                { percent: 5, label: '5% (Агрессивный)', desc: 'Максимум роста' }
              ].map((item) => (
                <button
                  key={item.percent}
                  onClick={() => setFlatPercent(item.percent)}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    flatPercent === item.percent
                      ? 'bg-gradient-to-r from-blue-600/30 to-cyan-600/30 border-cyan-400 text-white shadow-md shadow-cyan-500/10'
                      : 'bg-[#0a0f1d] border-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  <div className="text-xs font-black">{item.percent}% флэт</div>
                  <div className="text-[10px] text-gray-400 leading-tight mt-0.5">{item.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Average Odds */}
          <div>
            <label className="text-xs font-bold text-gray-300 uppercase tracking-wider block mb-1.5">
              Средний кэф ставки дня:
            </label>
            <div className="flex items-center gap-3">
              <input 
                type="range" 
                min="1.30" 
                max="3.50" 
                step="0.05"
                value={customOdds}
                onChange={(e) => setCustomOdds(parseFloat(e.target.value))}
                className="flex-1 accent-cyan-400 cursor-pointer"
              />
              <span className="font-mono font-black text-sm text-cyan-300 px-3 py-1 bg-cyan-950/80 rounded-lg border border-cyan-500/30">
                {customOdds.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Calculation Results Card */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-[#0a0f1d] via-[#101726] to-[#0a0f1d] border border-cyan-500/20 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Сумма 1 ставки (1 флэт):</span>
            <span className="font-black text-cyan-300 text-sm">{oneFlatAmount.toLocaleString()} ₽</span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Чистая прибыль с 1 победы:</span>
            <span className="font-black text-emerald-400 text-sm">+{potentialNetProfitPerBet.toLocaleString()} ₽</span>
          </div>

          <div className="pt-2 border-t border-gray-800 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-gray-300 block">Прогноз профита за месяц:</span>
              <span className="text-[11px] text-gray-500">По трек-рекорду (+{currentFlatProfit} флэт, {currentWinrate}%)</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-emerald-400 block font-heading">
                +{estimatedMonthProfit.toLocaleString()} ₽
              </span>
              <span className="text-[10px] font-bold text-cyan-300">+{growthPercent}% к банку</span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="mt-4 pt-3 flex items-center justify-between text-[11px] text-gray-400">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Дисциплина флэта защищает от просадок</span>
          </span>
          <button 
            onClick={onClose}
            className="text-xs font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            <span>Понятно</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
