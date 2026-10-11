import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const getTopBets = async (sportType = null, date = null, statusFilter = null) => {
  try {
    const params = {};
    if (sportType && sportType !== 'All') params.sport_type = sportType;
    if (date) params.date = date;
    if (statusFilter) params.status_filter = statusFilter;
    const response = await api.get('/predictions/top-daily', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching top bets:", error);
    throw error;
  }
};

export const getTodayMatches = async (sportType = null, date = null) => {
  try {
    const params = {};
    if (sportType && sportType !== 'All') params.sport_type = sportType;
    if (date) params.date = date;
    const response = await api.get('/predictions/today', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching today matches:", error);
    throw error;
  }
};

export const getPerformanceStats = async () => {
  try {
    const response = await api.get('/stats/overview');
    return response.data;
  } catch (error) {
    console.error("Error fetching performance stats:", error);
    return null;
  }
};

export const getRecentResults = async (sportType = null) => {
  try {
    const params = {};
    if (sportType && sportType !== 'All') params.sport_type = sportType;
    const response = await api.get('/results/recent', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching recent results:", error);
    return [];
  }
};

export const syncMatchResults = async () => {
  try {
    const response = await api.post('/results/sync');
    return response.data;
  } catch (error) {
    console.error("Error syncing match results:", error);
    throw error;
  }
};

export const getAiAnalysis = async (sportType = null, date = null) => {
  try {
    const params = {};
    if (sportType && sportType !== 'All') params.sport_type = sportType;
    if (date) params.date = date;
    // Увеличиваем таймаут для ИИ-запроса, так как он может отвечать дольше
    const response = await api.get('/ai-analyze-bets', { params, timeout: 30000 });
    return response.data;
  } catch (error) {
    console.error("Error fetching AI analysis:", error);
    throw error;
  }
};

export const getDailyParlays = async () => {
  try {
    const response = await api.get('/parlays/daily');
    return response.data;
  } catch (error) {
    console.error("Error fetching daily parlays:", error);
    return { safe_parlay: null, hot_parlay: null };
  }
};

export const sendParlayToTelegram = async (parlayType = 'safe') => {
  try {
    const response = await api.post(`/telegram/send-parlay?parlay_type=${parlayType}`);
    return response.data;
  } catch (error) {
    console.error("Error sending parlay to Telegram:", error);
    throw error;
  }
};

export const sendSuperAlerts = async () => {
  try {
    const response = await api.post('/telegram/send-super-alerts');
    return response.data;
  } catch (error) {
    console.error("Error triggering super alerts:", error);
    throw error;
  }
};

