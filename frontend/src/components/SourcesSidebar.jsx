import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, Clock, RefreshCw, Radio, X } from 'lucide-react';
import { API_BASE_URL } from '../api';

const SourcesSidebar = ({ isOpen, onClose }) => {
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

  // Закрытие по нажатию клавиши Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && onClose) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncMessage('Запуск сбора...');
    try {
      const res = await fetch(`${API_BASE_URL}/sources/sync`, { method: 'POST' });
      const data = await res.json();
      setSyncMessage('Сбор в процессе (1-2 мин)...');
      
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

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex justify-end bg-black/80 backdrop-blur-sm animate-fade-in transition-opacity"
      onClick={onClose}
    >
      <div 
        className="w-full sm:w-[440px] max-w-full h-full bg-gray-900 border-l border-gray-800 shadow-2xl flex flex-col p-5 overflow-hidden transition-transform duration-300"
        onClick={e => e.stopPropagation()}
      >
        {/* Заголовок и кнопка закрытия */}
        <div className="flex items-center justify-between gap-3 pb-4 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 bg-blue-500/15 border border-blue-500/25 rounded-2xl text-blue-400">
              <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-black text-white">Мониторинг Источников</h3>
              <p className="text-[11px] text-gray-400 mt-0.5">
                {onlineSources.length} активно сейчас • {sources.length} всего
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSync}
              disabled={isSyncing}
              title="Запустить немедленный парсинг всех источников"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 hover:text-blue-300 border border-blue-500/30 rounded-xl text-xs font-bold transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Сбор...' : 'Обновить'}</span>
            </button>

            <button
              onClick={onClose}
              title="Закрыть"
              className="p-1.5 text-gray-400 hover:text-white bg-gray-800/80 hover:bg-gray-700 rounded-xl transition-all border border-gray-700/80 shadow-sm"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {syncMessage && (
          <div className="mt-3 px-3 py-2 bg-blue-500/10 border border-blue-500/25 rounded-xl text-xs text-blue-300 flex items-center gap-2 shrink-0">
            <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
            <span>{syncMessage}</span>
          </div>
        )}

        {/* Быстрые фильтры и статистика */}
        <div className="flex gap-1.5 my-4 p-1 bg-gray-950/80 rounded-xl border border-gray-800 text-xs shrink-0">
          <button
            onClick={() => setFilter('all')}
            className={`flex-1 py-1.5 rounded-lg font-bold transition-all ${
              filter === 'all' 
                ? 'bg-gray-800 text-white shadow-sm' 
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Все ({sources.length})
          </button>
          <button
            onClick={() => setFilter('online')}
            className={`flex-1 py-1.5 rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 ${
              filter === 'online' 
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm' 
                : 'text-gray-400 hover:text-emerald-400'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Онлайн ({onlineSources.length})
          </button>
          <button
            onClick={() => setFilter('waiting')}
            className={`flex-1 py-1.5 rounded-lg font-bold transition-all ${
              filter === 'waiting' 
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm' 
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Ожидание ({waitingSources.length})
          </button>
        </div>

        {/* Список источников со стилизованным скроллом */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-gray-800 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent">
          {filteredSources.map(s => {
            const isOnline = s.recent_predictions_count > 0 || s.status.includes('Онлайн');

            return (
              <div 
                key={s.id} 
                className={`p-3.5 rounded-2xl border transition-all text-sm ${
                  isOnline 
                    ? 'bg-emerald-950/20 border-emerald-500/30 shadow-sm shadow-emerald-950/20' 
                    : 'bg-gray-950/50 border-gray-800/80 hover:border-gray-700/80'
                }`}
              >
                <div className="font-bold text-gray-200 mb-1 flex items-center justify-between">
                  <span className="truncate mr-2" title={s.name}>{s.name}</span>
                  {isOnline ? (
                    <span className="flex items-center gap-1 text-[11px] font-black text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/30 shrink-0">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Онлайн
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-400/80 bg-amber-500/5 px-2.5 py-0.5 rounded-full border border-amber-500/20 shrink-0">
                      <Clock className="w-3 h-3 text-amber-400/70" />
                      Ожидание
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-400 mt-2 pt-2 border-t border-gray-800/60">
                  <span className="text-gray-500 font-medium">
                    {s.source_type === 'telegram_channel' ? '📡 Telegram' : '🌐 Сайт/API'}
                  </span>
                  <span className={isOnline ? 'text-emerald-400 font-bold' : 'text-gray-500'}>
                    Прогнозов за 24ч: <strong className={isOnline ? 'text-white' : 'text-gray-400'}>{s.recent_predictions_count}</strong>
                  </span>
                </div>

                {s.last_parsed_at && (
                  <div className="text-[11px] text-gray-500 flex items-center gap-1 mt-1.5">
                    <Clock className="w-3 h-3 text-gray-600 shrink-0" />
                    <span>Обновлено: {new Date(s.last_parsed_at).toLocaleString([], {month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                )}
              </div>
            );
          })}

          {filteredSources.length === 0 && (
            <div className="text-center py-10 text-gray-500 text-xs">
              Нет источников в этой категории.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SourcesSidebar;
