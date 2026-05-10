import React, { useState, useEffect, useRef } from "react";
import { Link, NavLink, useSearchParams, useNavigate } from "react-router-dom";
import { getMatches } from "../../api";

// Логотипы лиг
import plLogo from "../../assets/leagues/premier-league.png";
import blLogo from "../../assets/leagues/bundesliga.png";
import saLogo from "../../assets/leagues/serie-a.png";
import pdLogo from "../../assets/leagues/la-liga.png";
import flLogo from "../../assets/leagues/ligue-1.png";

const leagues = [
  { code: null, name: "ВСЕ ЧЕМПИОНАТЫ", logo: null },
  { code: "Premier_League", name: "Premier League", logo: plLogo },
  { code: "La_Liga", name: "La Liga", logo: pdLogo },
  { code: "Serie_A", name: "Serie A", logo: saLogo },
  { code: "Bundesliga", name: "Bundesliga", logo: blLogo },
  { code: "Ligue_1", name: "Ligue 1", logo: flLogo },
];

function Header() {
  const [isLeagueOpen, setIsLeagueOpen] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const dropdownRef = useRef(null);
  const searchRef = useRef(null);

  // Состояния для поиска
  const [searchTerm, setSearchTerm] = useState(
    searchParams.get("search") || "",
  );
  const [allTeams, setAllTeams] = useState([]); // Здесь будут объекты { name, logo }
  const [suggestions, setSuggestions] = useState([]);
  const [isSuggestionsOpen, setIsSuggestionsOpen] = useState(false);

  // 1. Загрузка уникальных команд с ЛОГОТИПАМИ для автокомплита
  useEffect(() => {
    const fetchTeamsForAutocomplete = async () => {
      try {
        const data = await getMatches(null);
        const teamMap = new Map();

        data.forEach((m) => {
          // Сохраняем имя (RU/EN) и привязываем к нему логотип
          if (m.homeTeam?.name)
            teamMap.set(m.homeTeam.name, m.homeTeam.logo_url);
          if (m.homeTeam?.name_ru)
            teamMap.set(m.homeTeam.name_ru, m.homeTeam.logo_url);
          if (m.awayTeam?.name)
            teamMap.set(m.awayTeam.name, m.awayTeam.logo_url);
          if (m.awayTeam?.name_ru)
            teamMap.set(m.awayTeam.name_ru, m.awayTeam.logo_url);
        });

        const teamsArray = Array.from(teamMap.entries()).map(
          ([name, logo]) => ({ name, logo }),
        );
        setAllTeams(teamsArray);
      } catch (e) {
        console.error("Ошибка загрузки команд для поиска:", e);
      }
    };
    fetchTeamsForAutocomplete();
  }, []);

  // 2. Синхронизация инпута с URL
  useEffect(() => {
    setSearchTerm(searchParams.get("search") || "");
  }, [searchParams]);

  // 3. Закрытие выпадающих меню при клике вне их области
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsLeagueOpen(false);
      }
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsSuggestionsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 4. Обработка ввода (Фильтрация объектов)
  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);

    if (value.length > 0) {
      const filtered = allTeams
        .filter((t) => t.name.toLowerCase().includes(value.toLowerCase()))
        .slice(0, 10);
      setSuggestions(filtered);
      setIsSuggestionsOpen(true);
    } else {
      setIsSuggestionsOpen(false);
    }
  };

  // 5. Выполнение поиска
  const executeSearch = (query) => {
    setSearchTerm(query);
    setIsSuggestionsOpen(false);
    if (query) {
      navigate(`/?search=${encodeURIComponent(query)}`);
    } else {
      navigate(`/`);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    executeSearch(searchTerm);
  };

  const currentLeagueCode = searchParams.get("league");
  const activeLeague =
    leagues.find((l) => l.code === currentLeagueCode) || leagues[0];

  return (
    <header className="bg-gray-950 border-b border-gray-900 sticky top-0 z-[100] w-full">
      <div className="container mx-auto px-4 h-24 flex items-center justify-between gap-4">
        {/* ЛОГОТИП */}
        <Link to="/" className="flex-shrink-0">
          <span className="text-xl lg:text-2xl font-black tracking-tighter text-gradient-neuro-title uppercase italic">
            Neuro<span className="text-red-600">Predict</span>
          </span>
        </Link>

        {/* ЦЕНТРАЛЬНЫЙ ПОИСК С ЛОГОТИПАМИ В ПОДСКАЗКАХ */}
        <div
          className="flex-grow max-w-xs md:max-w-md relative mx-2"
          ref={searchRef}
        >
          <form onSubmit={handleFormSubmit} className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={handleInputChange}
              onFocus={() => {
                if (searchTerm.length > 0) setIsSuggestionsOpen(true);
              }}
              autoComplete="off"
              placeholder="Поиск команды..."
              className="w-full bg-gray-900 border border-gray-800 rounded-xl py-3 px-5 text-sm text-gray-300 focus:outline-none focus:border-red-600 transition-all font-bold"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => executeSearch("")}
                className="absolute right-12 top-3 text-gray-600 hover:text-white transition-colors"
              >
                ✕
              </button>
            )}
            <button
              type="submit"
              className="absolute right-4 top-3 text-gray-600 hover:text-red-600 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </form>

          {/* ВЫПАДАЮЩИЙ СПИСОК С ЭМБЛЕМАМИ */}
          {isSuggestionsOpen && suggestions.length > 0 && (
            <ul className="absolute top-full left-0 right-0 mt-2 bg-gray-950 border border-gray-800 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.7)] overflow-hidden z-50">
              {suggestions.map((team, index) => (
                <li key={index}>
                  <button
                    onClick={() => executeSearch(team.name)}
                    className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-red-600 transition-all border-b border-gray-900 last:border-0 group"
                  >
                    <img
                      src={team.logo}
                      alt=""
                      className="w-8 h-8 object-contain group-hover:scale-110 transition-transform"
                    />
                    <span className="text-sm font-black uppercase text-gray-300 group-hover:text-white">
                      {team.name}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* ПРАВАЯ ЧАСТЬ (СРАВНЕНИЕ И ЛИГИ) */}
        <div className="flex items-center gap-2" ref={dropdownRef}>
          <Link
            to="/compare"
            className="flex items-center gap-2 px-3 py-2.5 bg-gray-900 border border-gray-800 rounded-xl hover:border-red-600 transition-all group shadow-lg"
          >
            <span className="hidden sm:block text-[10px] font-black uppercase text-gray-400 group-hover:text-white tracking-widest">
              Сравнение
            </span>
          </Link>

          <div className="relative">
            <button
              onClick={() => setIsLeagueOpen(!isLeagueOpen)}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border-2 transition-all ${
                isLeagueOpen
                  ? "bg-red-600 border-red-600"
                  : "bg-gray-900 border-gray-800 text-gray-300 hover:border-gray-600"
              }`}
            >
              <span className="hidden lg:block text-[10px] font-black uppercase tracking-widest">
                {activeLeague.code ? activeLeague.name : "Чемпионаты"}
              </span>
              <svg
                className={`w-4 h-4 transition-transform ${isLeagueOpen ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="3"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {isLeagueOpen && (
              <div className="absolute top-full right-0 mt-3 w-[280px] bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2">
                <div className="flex flex-col p-2 space-y-1">
                  {leagues.map((league) => {
                    const isActive =
                      currentLeagueCode === league.code ||
                      (!currentLeagueCode && league.code === null);
                    return (
                      <NavLink
                        key={league.code || "all"}
                        to={league.code ? `/?league=${league.code}` : "/"}
                        className={`flex items-center gap-4 px-3 py-3 rounded-xl transition-all ${
                          isActive
                            ? "bg-red-600 text-white"
                            : "text-gray-400 hover:bg-gray-900 hover:text-white"
                        }`}
                      >
                        <div
                          className={`w-14 h-14 rounded-lg flex items-center justify-center flex-shrink-0 bg-white`}
                        >
                          {league.logo ? (
                            <img
                              src={league.logo}
                              alt=""
                              className="w-10 h-10 object-contain"
                            />
                          ) : (
                            <span className="text-xs font-black text-yellow-500">
                              ALL
                            </span>
                          )}
                        </div>
                        <span className="text-xs font-black uppercase tracking-tight">
                          {league.name}
                        </span>
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
