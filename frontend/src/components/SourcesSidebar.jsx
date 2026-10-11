import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, Clock, RefreshCw, Radio, Sparkles } from 'lucide-react';
import { API_BASE_URL } from '../api';

const SourcesSidebar = () => {
  const [sources, setSources] = useState([]);
  const [filter, setFilter] = useState('all'); // 'all' | 'online' | 'waiting'
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const loadData = () => {
    fetch(`${API_BASE_URL}/sources/status`)
      .then(r => r.json())
      .then(data => setSources(data))
      .catch(e => console.error(e));
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000); // Опрос каждые 15 сек
    return () => clearInterval(interval);
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncMessage('Запуск сбора...');
    try {
      const res = await fetch(`${API_BASE_URL}/sources/sync`, { method: 'POST' });
      const data = await res.json();
      setSyncMessage('Сбор в процессе (1-2 мин)...');
      
      // Частый опрос статуса после запуска
      let attempts = 0;
      const pollInterval = setInterval(() => {
        loadData();
        attempts++;
        if (attempts >= 10) {
          clearInterval(pollInterval);
          setIsSyncing(false);
          setSyncMessage('');
        }
      }, 5000);
    } catch (e) {
      console.error(e);
      setSyncMessage('Ошибка запуска');
      setTimeout(() => setIsSyncing(false), 3000);
    }
  };

  const onlineSources = sources.filter(s => s.recent_predictions_count > 0 || s.status.includes('Онлайн'));
  const waitingSources = sources.filter(s => s.recent_predictions_count === 0 && !s.status.includes('Онлайн'));

  const filteredSources = filter === 'online' 
    ? onlineSources 
    : filter === 'waiting' 
    ? waitingSources 
    : sources;

  return (
    <div className="w-full lg:w-80 shrink-0 bg-card border border-gray-800 rounded-2xl p-4 overflow-y-auto max-h-[calc(100vh-100px)] lg:sticky top-24 shadow-xl">
      {/* Заголовок и кнопка синхронизации */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 text-gray-100 font-bold text-base">
          <Activity className="w-5 h-5 text-blue-400" />
          <h3>Дебаг Источников</h3>
        </div>
        <button
          onClick={handleSync}
          disabled={isSyncing}
          title="Запустить немедленный парсинг всех источников"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 hover:text-blue-300 border border-blue-500/30 rounded-xl text-xs font-semibold transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Сбор...' : 'Обновить'}</span>
        </button>
      </div>

      {syncMessage && (
        <div className="mb-3 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-300 flex items-center gap-2">
          <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <span>{syncMessage}</span>
        </div>
      )}

      {/* Быстрые фильтры и статистика */}
      <div className="flex gap-1.5 mb-4 p-1 bg-gray-900/60 rounded-xl border border-gray-800 text-xs">
        <button
          onClick={() => setFilter('all')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-colors ${
            filter === 'all' ? 'bg-gray-800 text-white shadow' : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          Все ({sources.length})
        </button>
        <button
          onClick={() => setFilter('online')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-1 ${
            filter === 'online' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'text-gray-400 hover:text-emerald-400'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Онлайн ({onlineSources.length})
        </button>
        <button
          onClick={() => setFilter('waiting')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-colors ${
            filter === 'waiting' ? 'bg-gray-800 text-amber-300' : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          Ожидание ({waitingSources.length})
        </button>
      </div>

      {/* Список источников */}
      <div className="space-y-2.5">
        {filteredSources.map(s => {
          const isOnline = s.recent_predictions_count > 0 || s.status.includes('Онлайн');

          return (
            <div 
              key={s.id} 
              className={`p-3 rounded-xl border transition-all text-sm ${
                isOnline 
                  ? 'bg-emerald-950/20 border-emerald-500/30 shadow-sm shadow-emerald-950/30' 
                  : 'bg-gray-900/40 border-gray-800/80'
              }`}
            >
              <div className="font-semibold text-gray-200 mb-1 flex items-center justify-between">
                <span className="truncate mr-2" title={s.name}>{s.name}</span>
                {isOnline ? (
                  <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Онлайн
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-medium text-amber-400/80 bg-amber-500/5 px-2 py-0.5 rounded-full border border-amber-500/20">
                    <Clock className="w-3 h-3 text-amber-400/70" />
                    Ожидание
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-gray-400 mt-2 pt-2 border-t border-gray-800/60">
                <span className="text-gray-500">
                  {s.source_type === 'telegram_channel' ? '📡 Telegram' : '🌐 Сайт/API'}
                </span>
                <span className={isOnline ? 'text-emerald-400 font-bold' : 'text-gray-500'}>
                  24ч: <strong className={isOnline ? 'text-white' : 'text-gray-400'}>{s.recent_predictions_count}</strong>
                </span>
              </div>

              {s.last_parsed_at && (
                <div className="text-[11px] text-gray-500 flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3 text-gray-600" />
                  <span>Обновлено: {new Date(s.last_parsed_at).toLocaleString([], {month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'})}</span>
                </div>
              )}
            </div>
          );
        })}

        {filteredSources.length === 0 && (
          <div className="text-center py-6 text-gray-500 text-xs">
            Нет источников в этой категории.
          </div>
        )}
      </div>
    </div>
  );
};

export default SourcesSidebar;
