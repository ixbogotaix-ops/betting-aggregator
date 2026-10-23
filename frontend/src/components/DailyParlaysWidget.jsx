import React, { useState, useEffect } from 'react';
import { 
  Zap, Shield, Flame, Check, Copy, Send, RefreshCw, 
  TrendingUp, Calculator, ArrowRight, CheckCircle2, AlertCircle 
} from 'lucide-react';
import { getDailyParlays, sendParlayToTelegram, sendSuperAlerts } from '../api';
import { formatLeagueDisplay } from './TopBetCard';
import { toRussianMatchName, toRussianLeague } from '../utils/russianNames';

export default function DailyParlaysWidget() {
  const [parlays, setParlays] = useState({ ai_parlay: null, safe_parlay: null, hot_parlay: null });
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('ai'); // 'ai' | 'safe' | 'hot'
  const [betAmount, setBetAmount] = useState(1000);
  const [enabledLegIds, setEnabledLegIds] = useState(new Set());
  const [copied, setCopied] = useState(false);
  const [sendingTg, setSendingTg] = useState(false);
  const [tgFeedback, setTgFeedback] = useState(null);
  const [sendingAlerts, setSendingAlerts] = useState(false);
  const [alertsFeedback, setAlertsFeedback] = useState(null);

  const fetchParlays = async () => {
    setLoading(true);
    try {
      const data = await getDailyParlays();
      setParlays(data);
      // Приоритет выбора: ai -> safe -> hot
      const initialType = data.ai_parlay ? 'ai' : (data.safe_parlay ? 'safe' : 'hot');
      setSelectedType(initialType);
      const activeParlay = initialType === 'ai' ? data.ai_parlay : (initialType === 'safe' ? data.safe_parlay : data.hot_parlay);
      if (activeParlay && activeParlay.items) {
        setEnabledLegIds(new Set(activeParlay.items.map(it => it.match_id)));
      }
    } catch (err) {
      console.error("Ошибка загрузки экспрессов:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParlays();
  }, []);

  // При смене вкладки сбрасываем активные чекбоксы на все матчи нового экспресса
  const handleTypeChange = (type) => {
    setSelectedType(type);
    const target = type === 'ai' ? parlays.ai_parlay : (type === 'safe' ? parlays.safe_parlay : parlays.hot_parlay);
    if (target && target.items) {
      setEnabledLegIds(new Set(target.items.map(it => it.match_id)));
    }
    setTgFeedback(null);
  };

  const currentParlay = selectedType === 'ai' ? parlays.ai_parlay : (selectedType === 'safe' ? parlays.safe_parlay : parlays.hot_parlay);

  // Переключение чекбокса отдельного события
  const toggleLeg = (matchId) => {
    setEnabledLegIds(prev => {
      const next = new Set(prev);
      if (next.has(matchId)) {
        if (next.size <= 1) return prev; // Не даем убрать последний оставшийся матч
        next.delete(matchId);
      } else {
        next.add(matchId);
      }
      return next;
    });
  };

  // Расчет динамического коэффициента с учетом включенных чекбоксов
  const activeItems = (currentParlay?.items || []).filter(item => enabledLegIds.has(item.match_id));
  const dynamicOdds = activeItems.reduce((acc, it) => acc * (it.odds || 1.0), 1.0);
  const totalOddsDisplay = activeItems.length > 0 ? dynamicOdds.toFixed(2) : "1.00";
  const potentialWin = Math.round((Number(betAmount) || 0) * dynamicOdds);
  const netProfit = Math.max(0, potentialWin - (Number(betAmount) || 0));

  // Копирование купона в буфер обмена
  const handleCopySlip = () => {
    if (!currentParlay || activeItems.length === 0) return;
    
    let text = `⚡ ${currentParlay.title.toUpperCase()} (AI Sports Aggregator)\n`;
    text += `📈 Общий кэф: ${totalOddsDisplay}\n`;
    text += `💵 Ставка: ${betAmount.toLocaleString('ru-RU')} ₽ | Возможный выигрыш: ${potentialWin.toLocaleString('ru-RU')} ₽\n\n`;
    text += `📋 События:\n`;
    
    activeItems.forEach((it, idx) => {
      const timeStr = it.match_date ? new Date(it.match_date).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : '';
      text += `${idx + 1}. ${it.match_name} ${timeStr ? `(${timeStr} МСК)` : ''}\n`;
      text += `   🎯 Исход: ${it.outcome} | Кэф: ${it.odds} | Уверенность: ${it.confidence_score}%\n`;
    });
    
    text += `\n🌐 Платформа: http://45.84.222.76`;

    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  // Отправка экспресса в Telegram
  const handleSendToTelegram = async () => {
    setSendingTg(true);
    setTgFeedback(null);
    try {
      const res = await sendParlayToTelegram(selectedType);
      if (res.status === 'ok') {
        setTgFeedback({ type: 'success', message: 'Экспресс успешно отправлен в Telegram канал!' });
      } else {
        setTgFeedback({ type: 'error', message: res.message || 'Ошибка отправки' });
      }
    } catch (err) {
      setTgFeedback({ type: 'error', message: 'Не удалось отправить экспресс в Telegram' });
    } finally {
      setSendingTg(false);
      setTimeout(() => setTgFeedback(null), 5000);
    }
  };

  // Срочный вызов супер-алертов в Telegram
  const handleTriggerSuperAlerts = async () => {
    setSendingAlerts(true);
    setAlertsFeedback(null);
    try {
      const res = await sendSuperAlerts();
      if (res.status === 'ok') {
        const count = res.sent_alerts_count || 0;
        setAlertsFeedback({ 
          type: 'success', 
          message: count > 0 
            ? `Отправлено ${count} срочных алертов супер-консенсуса в Telegram!` 
            : 'Все актуальные супер-консенсусы уже были отправлены ранее (без спама).' 
        });
      }
    } catch (err) {
      setAlertsFeedback({ type: 'error', message: 'Ошибка отправки супер-алертов' });
    } finally {
      setSendingAlerts(false);
      setTimeout(() => setAlertsFeedback(null), 5000);
    }
  };

  if (loading) {
    return (
      <div className="p-8 bg-card rounded-2xl border border-gray-800 animate-pulse text-center text-gray-500">
        <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-accent" />
        <p className="font-semibold text-gray-300">ИИ анализирует сотни матчей и собирает лучшие экспрессы дня...</p>
      </div>
    );
  }

  if (!parlays.ai_parlay && !parlays.safe_parlay && !parlays.hot_parlay) {
    return (
      <div className="p-8 bg-card rounded-2xl border border-gray-800 text-center">
        <AlertCircle className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
        <h3 className="text-lg font-bold text-gray-200">Экспрессы формируются</h3>
        <p className="text-sm text-gray-400 mt-1">
          Сейчас в линии недостаточно завершенных согласований между моделями. Запустите сбор или подождите формирования матчей.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-card via-gray-900 to-[#121622] rounded-3xl border border-gray-800 p-5 sm:p-7 shadow-2xl relative overflow-hidden mb-8">
      {/* Фоновое свечение */}
      <div className={`absolute -top-24 -right-24 w-80 h-80 rounded-full blur-3xl opacity-20 pointer-events-none transition-colors duration-500 ${
        selectedType === 'ai' ? 'bg-purple-500' : (selectedType === 'safe' ? 'bg-emerald-500' : 'bg-orange-500')
      }`} />
      
      {/* Шапка виджета */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 relative z-10 border-b border-gray-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className={`p-2 rounded-xl text-white shadow-lg ${
              selectedType === 'ai'
                ? 'bg-gradient-to-r from-purple-600 to-pink-500 shadow-purple-500/20'
                : selectedType === 'safe'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-500 shadow-emerald-500/20'
                  : 'bg-gradient-to-r from-orange-600 to-red-500 shadow-orange-500/20'
            }`}>
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                Умный Экспресс Дня
                <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  AI Multi-Bet
                </span>
              </h2>
              <p className="text-xs sm:text-sm text-gray-400 mt-0.5">
                Математически оптимизированные купоны на основе консенсуса прогнозистов и суперкомпьютера ИИ
              </p>
            </div>
          </div>
        </div>

        {/* Переключатель табов: Экспресс Тройного ИИ vs Надёжный vs Огненный */}
        <div className="flex flex-wrap items-center gap-2 p-1.5 bg-gray-950/80 rounded-2xl border border-gray-800 shrink-0 self-start md:self-auto">
          {parlays.ai_parlay && (
            <button
              onClick={() => handleTypeChange('ai')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                selectedType === 'ai'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/20 ring-1 ring-purple-400/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
              }`}
            >
              <Zap className="w-4 h-4 text-purple-300" />
              <span>🔥 ИИ-Экспресс</span>
              <span className="ml-1 text-[11px] px-1.5 py-0.2 bg-black/30 rounded font-black text-purple-200">
                x{parlays.ai_parlay.total_odds}
              </span>
            </button>
          )}

          {parlays.safe_parlay && (
            <button
              onClick={() => handleTypeChange('safe')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                selectedType === 'safe'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/20 ring-1 ring-emerald-400/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
              }`}
            >
              <Shield className="w-4 h-4 text-emerald-300" />
              <span>🛡️ Надёжный</span>
              <span className="ml-1 text-[11px] px-1.5 py-0.2 bg-black/30 rounded font-black text-emerald-200">
                x{parlays.safe_parlay.total_odds}
              </span>
            </button>
          )}

          {parlays.hot_parlay && (
            <button
              onClick={() => handleTypeChange('hot')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                selectedType === 'hot'
                  ? 'bg-gradient-to-r from-orange-600 to-red-600 text-white shadow-lg shadow-orange-500/20 ring-1 ring-orange-400/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
              }`}
            >
              <Flame className="w-4 h-4 text-orange-300" />
              <span>🚀 Огненный</span>
              <span className="ml-1 text-[11px] px-1.5 py-0.2 bg-black/30 rounded font-black text-orange-200">
                x{parlays.hot_parlay.total_odds}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Основная часть: список матчей в экспрессе + калькулятор */}
      {currentParlay ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
          
          {/* Левая колонка: Список событий экспресса (8 из 12 колонок) */}
          <div className="lg:col-span-7 xl:col-span-8 space-y-3">
            <div className="flex items-center justify-between text-xs text-gray-400 font-semibold px-1">
              <span>События в купоне ({activeItems.length} из {currentParlay.items.length}):</span>
              <span className="text-gray-500">Нажмите чекбокс, чтобы исключить событие</span>
            </div>

            {currentParlay.items.map((item) => {
              const isChecked = enabledLegIds.has(item.match_id);
              const timeFormatted = item.match_date 
                ? new Date(item.match_date).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) 
                : '';
              
              return (
                <div
                  key={item.match_id}
                  onClick={() => toggleLeg(item.match_id)}
                  className={`p-3.5 sm:p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between gap-3 ${
                    isChecked
                      ? 'bg-gray-900/90 border-gray-700/80 hover:border-gray-600 shadow-md'
                      : 'bg-gray-950/40 border-gray-900 opacity-50 line-through-text hover:opacity-75'
                  }`}
                >
                  {/* Чекбокс */}
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                      isChecked 
                        ? (selectedType === 'safe' ? 'bg-emerald-500 text-black' : 'bg-orange-500 text-white')
                        : 'border border-gray-700 bg-gray-950'
                    }`}>
                      {isChecked && <Check className="w-4 h-4 stroke-[3]" />}
                    </div>

                    {/* Матч и команды */}
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 text-xs text-gray-400 mb-0.5">
                        <span className="font-semibold text-gray-300">{toRussianLeague(item.league)}</span>
                        {timeFormatted && <span>• {timeFormatted} МСК</span>}
                        <span className="text-[10px] px-1.5 py-0.2 bg-blue-500/10 text-blue-400 rounded">
                          {item.sport_type}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2 font-black text-sm sm:text-base text-white truncate font-heading tracking-tight">
                        <span className="truncate">{toRussianMatchName(item.match_name)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Выбор (исход) и коэффициент */}
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-bold text-gray-200">
                        {item.outcome}
                      </div>
                      <div className="text-[11px] text-emerald-400 font-semibold">
                        {item.confidence_score}% консенсус
                      </div>
                    </div>

                    <div className={`px-2.5 py-1.5 rounded-xl font-black text-sm sm:text-base border shadow-inner ${
                      isChecked
                        ? (selectedType === 'safe' 
                            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300' 
                            : 'bg-orange-950/40 border-orange-500/30 text-orange-300')
                        : 'bg-gray-900 border-gray-800 text-gray-500'
                    }`}>
                      {item.odds}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Правая колонка: Интерактивный Калькулятор Выигрыша (5 из 12 колонок) */}
          <div className="lg:col-span-5 xl:col-span-4 flex flex-col justify-between p-5 bg-gray-950/80 rounded-2xl border border-gray-800/90 shadow-xl">
            <div>
              <div className="flex items-center gap-2 mb-4 text-gray-300 font-bold text-sm">
                <Calculator className="w-4 h-4 text-accent" />
                <span>Калькулятор экспресса</span>
              </div>

              {/* Карточка итогового коэффициента */}
              <div className="p-4 rounded-xl bg-gray-900/90 border border-gray-800 mb-4 flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-400 font-medium">Общий коэффициент</div>
                  <div className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-1.5 mt-0.5">
                    <span className="text-accent">x</span>
                    <span>{totalOddsDisplay}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400 font-medium">Событий в купоне</div>
                  <div className="text-xl font-bold text-gray-200 mt-0.5">
                    {activeItems.length} шт.
                  </div>
                </div>
              </div>

              {/* Выбор суммы ставки */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                  Сумма ставки (₽):
                </label>
                <div className="relative">
                  <input
                    type="number"
                    min="50"
                    step="100"
                    value={betAmount}
                    onChange={(e) => setBetAmount(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-full bg-gray-900 border border-gray-700/80 rounded-xl px-3.5 py-2.5 text-white font-bold text-lg outline-none focus:border-accent"
                  />
                  <span className="absolute right-3.5 top-3 text-sm font-bold text-gray-400">₽</span>
                </div>

                {/* Быстрые пресеты */}
                <div className="grid grid-cols-4 gap-1.5 mt-2">
                  {[500, 1000, 2500, 5000].map(amt => (
                    <button
                      key={amt}
                      onClick={() => setBetAmount(amt)}
                      className={`py-1 rounded-lg text-xs font-bold transition-colors ${
                        betAmount === amt 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-900 text-gray-400 hover:text-white hover:bg-gray-800'
                      }`}
                    >
                      {amt.toLocaleString('ru-RU')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Расчет выигрыша */}
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/40 to-teal-950/30 border border-emerald-500/20 mb-5">
                <div className="flex items-center justify-between text-xs text-emerald-400 font-medium mb-1">
                  <span>Возможный выигрыш:</span>
                  <span className="font-bold">+{netProfit.toLocaleString('ru-RU')} ₽ чистыми</span>
                </div>
                <div className="text-2xl sm:text-3xl font-black text-emerald-300 tracking-tight">
                  {potentialWin.toLocaleString('ru-RU')} ₽
                </div>
              </div>
            </div>

            {/* Кнопки действий */}
            <div className="space-y-2">
              <button
                onClick={handleCopySlip}
                disabled={activeItems.length === 0}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20 transition-all active:scale-[0.98] disabled:opacity-50"
              >
                {copied ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                    <span>Купон скопирован в буфер!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Скопировать готовый купон</span>
                  </>
                )}
              </button>

              <button
                onClick={handleSendToTelegram}
                disabled={sendingTg || activeItems.length === 0}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-bold text-xs bg-gray-900 hover:bg-gray-800 text-gray-200 border border-gray-700/60 transition-all disabled:opacity-50"
              >
                <Send className={`w-3.5 h-3.5 text-blue-400 ${sendingTg ? 'animate-bounce' : ''}`} />
                <span>{sendingTg ? 'Отправляем...' : 'Опубликовать экспресс в Telegram'}</span>
              </button>

              <a
                href="https://t.me/DthenBK_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl font-bold text-xs bg-blue-600/15 hover:bg-blue-600/25 text-blue-300 border border-blue-500/30 transition-all text-center"
              >
                <Send className="w-3.5 h-3.5 text-blue-400" />
                <span>Запустить бота в Telegram (@DthenBK_bot)</span>
              </a>

              {tgFeedback && (
                <div className={`p-2 rounded-lg text-xs text-center font-semibold ${
                  tgFeedback.type === 'success' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                }`}>
                  {tgFeedback.message}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {/* Нижняя панель быстрых действий: ручной вызов супер-алертов */}
      <div className="mt-6 pt-4 border-t border-gray-800/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-400 relative z-10">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Срочные алерты в Telegram отправляются автоматически при консенсусе от 4+ источников или уверенности &gt; 85%.</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleTriggerSuperAlerts}
            disabled={sendingAlerts}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 border border-gray-700 text-gray-300 hover:text-white transition-colors"
          >
            <Send className="w-3 h-3 text-amber-400" />
            <span>{sendingAlerts ? 'Проверка...' : 'Проверить и отправить супер-алерты'}</span>
          </button>
        </div>
      </div>

      {alertsFeedback && (
        <div className={`mt-2 p-2 rounded-lg text-xs text-center font-semibold relative z-10 ${
          alertsFeedback.type === 'success' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
        }`}>
          {alertsFeedback.message}
        </div>
      )}
    </div>
  );
}
