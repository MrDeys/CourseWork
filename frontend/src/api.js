import axios from "axios";

const API_BASE_URL = "/api";

const parseData = (data) => {
  if (typeof data === "string") {
    try {
      return JSON.parse(data);
    } catch (e) {
      console.error("Ошибка парсинга JSON строки от API:", e);
      return null;
    }
  }
  return data;
};

export const getMatches = async (leagueCode = null) => {
  try {
    let url = `${API_BASE_URL}/matches/`;
    if (leagueCode) {
      url += `?league=${leagueCode}`;
    }
    const response = await axios.get(url);
    const parsedData = parseData(response.data);
    return Array.isArray(parsedData) ? parsedData : [];
  } catch (error) {
    console.error("Ошибка при загрузке списка матчей:", error);
    return [];
  }
};

export const getMatchId = async (matchId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/matches/${matchId}`);
    const parsedData = parseData(response.data);
    return parsedData;
  } catch (error) {
    console.error(`Ошибка при загрузке матча:`, error);
    return null;
  }
};

export const getLeagueTable = async (leagueName) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/matches/table/${leagueName}`,
    );
    return response.data;
  } catch (error) {
    console.error("Error fetching table:", error);
    return [];
  }
};

export const getTeamComparison = async (team1, team2) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/matches/compare`, {
      params: { team1, team2 },
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при сравнении команд:", error);
    return null;
  }
};
