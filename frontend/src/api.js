import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const getTopBets = async (sportType = null, date = null) => {
  try {
    const params = {};
    if (sportType && sportType !== 'All') params.sport_type = sportType;
    if (date) params.date = date;
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
