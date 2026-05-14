import axios from "axios";

//const API_BASE_URL = "/api";
const API_BASE_URL = "http://192.168.3.22:5000/api";
//const API_BASE_URL = "https://my-neuro-diploma-777.loca.lt/api";

// 2. Создаем специальный экземпляр axios с настройками для туннеля
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Bypass-Tunnel-Reminder": "true",
  },
});

// Умный парсер данных
const parseData = (data) => {
  if (typeof data === "string") {
    try {
      return JSON.parse(data);
    } catch (e) {
      console.error("Ошибка парсинга JSON:", e);
      return null;
    }
  }
  return data;
};

export const getMatches = async (leagueCode = null) => {
  try {
    // ВАЖНО: используем api.get, путь пишем ОТНОСИТЕЛЬНО baseURL
    let url = "/matches/";
    if (leagueCode) {
      url += `?league=${leagueCode}`;
    }
    const response = await api.get(url);
    const parsedData = parseData(response.data);
    return Array.isArray(parsedData) ? parsedData : [];
  } catch (error) {
    console.error("Ошибка при загрузке списка матчей:", error);
    return [];
  }
};

export const getMatchId = async (matchId) => {
  try {
    const response = await api.get(`/matches/${matchId}`);
    return parseData(response.data);
  } catch (error) {
    console.error(`Ошибка при загрузке матча:`, error);
    return null;
  }
};

export const getLeagueTable = async (leagueName) => {
  try {
    const response = await api.get(`/matches/table/${leagueName}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching table:", error);
    return [];
  }
};

export const getTeamComparison = async (team1, team2) => {
  try {
    const response = await api.get("/matches/compare", {
      params: { team1, team2 },
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при сравнении команд:", error);
    return null;
  }
};
