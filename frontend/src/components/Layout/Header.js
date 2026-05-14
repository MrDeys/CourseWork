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

  const [searchTerm, setSearchTerm] = useState(
    searchParams.get("search") || "",
  );
  const [allTeams, setAllTeams] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isSuggestionsOpen, setIsSuggestionsOpen] = useState(false);

  useEffect(() => {
    const fetchTeamsForAutocomplete = async () => {
      try {
        const data = await getMatches(null);
        const teamMap = new Map();
        data.forEach((m) => {
          if (m.homeTeam?.name)
            teamMap.set(m.homeTeam.name, m.homeTeam.logo_url);
          if (m.homeTeam?.name_ru)
            teamMap.set(m.homeTeam.name_ru, m.homeTeam.logo_url);
          if (m.awayTeam?.name)
            teamMap.set(m.awayTeam.name, m.awayTeam.logo_url);
          if (m.awayTeam?.name_ru)
            teamMap.set(m.awayTeam.name_ru, m.awayTeam.logo_url);
        });
        setAllTeams(
          Array.from(teamMap.entries()).map(([name, logo]) => ({ name, logo })),
        );
      } catch (e) {
        console.error("Ошибка поиска:", e);
      }
    };
    fetchTeamsForAutocomplete();
  }, []);

  useEffect(() => {
    setSearchTerm(searchParams.get("search") || "");
  }, [searchParams]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target))
        setIsLeagueOpen(false);
      if (searchRef.current && !searchRef.current.contains(event.target))
        setIsSuggestionsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    if (value.length > 0) {
      setSuggestions(
        allTeams
          .filter((t) => t.name.toLowerCase().includes(value.toLowerCase()))
          .slice(0, 8),
      );
      setIsSuggestionsOpen(true);
    } else {
      setIsSuggestionsOpen(false);
    }
  };

  const executeSearch = (query) => {
    setSearchTerm(query);
    setIsSuggestionsOpen(false);
    if (query) navigate(`/?search=${encodeURIComponent(query)}`);
    else navigate(`/`);
  };

  const currentLeagueCode = searchParams.get("league");
  const activeLeague =
    leagues.find((l) => l.code === currentLeagueCode) || leagues[0];

  return (
    <header className="hidden md:block bg-gray-950 border-b border-gray-900 sticky top-0 z-[100] w-full shadow-2xl">
      <header className="bg-gray-950 border-b border-gray-900 sticky top-0 z-[100] w-full shadow-2xl">
        <div className="container mx-auto px-4 h-20 lg:h-24 flex items-center justify-between gap-2 lg:gap-4">
          {/* ЛОГОТИП: Сокращаем на мобилках до NP */}
          {/* ЛОГОТИП: Красно-желтый градиент (NP / NeuroPredict) */}
          <Link to="/" className="flex-shrink-0 group">
            <span className="text-2xl md:text-3xl font-black tracking-tighter uppercase italic flex items-center">
              {/* --- ВЕРСИЯ ДЛЯ ТЕЛЕФОНА (NP) --- */}
              <span className="md:hidden flex items-center">
                {/* N с градиентом от желтого к красному */}
                <span className="bg-gradient-to-b from-yellow-400 to-red-600 bg-clip-text text-transparent">
                  N
                </span>
                {/* P ярко-красная */}
                <span className="text-red-600">P</span>
              </span>

              {/* --- ВЕРСИЯ ДЛЯ ПК (NeuroPredict) --- */}
              <span className="hidden md:flex items-center transition-transform group-hover:scale-105">
                {/* Neuro: сочный градиент от желтого к красному */}
                <span className="bg-gradient-to-r from-yellow-400 via-orange-500 to-red-600 bg-clip-text text-transparent">
                  Neuro
                </span>
                {/* Predict: классический красный */}
                <span className="text-red-600 ml-px">Predict</span>
              </span>
            </span>
          </Link>

          {/* ПОИСК: Более гибкий под размер экрана */}
          <div
            className="flex-grow max-w-[150px] xs:max-w-xs md:max-w-md relative"
            ref={searchRef}
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                executeSearch(searchTerm);
              }}
              className="relative"
            >
              <input
                type="text"
                value={searchTerm}
                onChange={handleInputChange}
                onFocus={() =>
                  searchTerm.length > 0 && setIsSuggestionsOpen(true)
                }
                placeholder="Поиск..."
                className="w-full bg-gray-900 border border-gray-800 rounded-xl py-2 lg:py-3 pl-4 pr-9 text-xs lg:text-sm text-gray-300 focus:outline-none focus:border-red-600 transition-all font-bold"
              />
              <button
                type="submit"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-red-600"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="3"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </button>
            </form>

            {/* Подсказки поиска (адаптированные) */}
            {isSuggestionsOpen && suggestions.length > 0 && (
              <ul className="absolute top-full left-0 right-0 mt-2 bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden z-50">
                {suggestions.map((team, index) => (
                  <li key={index}>
                    <button
                      onClick={() => executeSearch(team.name)}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-red-600 transition-all border-b border-gray-900 last:border-0"
                    >
                      <img
                        src={team.logo}
                        alt=""
                        className="w-6 h-6 object-contain"
                      />
                      <span className="text-[10px] lg:text-xs font-black uppercase text-gray-300">
                        {team.name}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* КНОПКИ ДЕЙСТВИЙ */}
          <div className="flex items-center gap-1.5 lg:gap-3" ref={dropdownRef}>
            {/* Сравнение: Иконка на мобильном, текст на десктопе */}
            <Link
              to="/compare"
              className="flex items-center justify-center p-2.5 lg:px-4 lg:py-2.5 bg-gray-900 border border-gray-800 rounded-xl hover:border-red-600 transition-all group shadow-lg"
              title="Сравнение команд"
            >
              <svg
                className="w-5 h-5 lg:mr-2 text-gray-400 group-hover:text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <span className="hidden lg:block text-[10px] font-black uppercase text-gray-400 group-hover:text-white tracking-widest">
                Сравнение
              </span>
            </Link>

            {/* Выбор Лиги */}
            <div className="relative">
              <button
                onClick={() => setIsLeagueOpen(!isLeagueOpen)}
                className={`flex items-center justify-center p-2.5 lg:px-4 lg:py-2.5 rounded-xl border-2 transition-all ${
                  isLeagueOpen
                    ? "bg-red-600 border-red-600 text-white"
                    : "bg-gray-900 border-gray-800 text-gray-300"
                }`}
              >
                {/* Показываем логотип активной лиги на мобилке вместо текста */}
                {activeLeague.logo ? (
                  <img
                    src={activeLeague.logo}
                    alt=""
                    className="w-5 h-5 lg:mr-2 object-contain"
                  />
                ) : (
                  <span className="lg:mr-2 text-[10px] font-black">ALL</span>
                )}
                <span className="hidden lg:block text-[10px] font-black uppercase tracking-widest">
                  {activeLeague.code ? activeLeague.name : "Лиги"}
                </span>
                <svg
                  className={`w-3 h-3 ml-1 transition-transform ${isLeagueOpen ? "rotate-180" : ""}`}
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

              {/* Выпадающий список (теперь закрывается при клике) */}
              {isLeagueOpen && (
                <div className="absolute top-full right-0 mt-3 w-[240px] lg:w-[280px] bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2">
                  <div className="flex flex-col p-1.5 space-y-1">
                    {leagues.map((league) => {
                      const isActive =
                        currentLeagueCode === league.code ||
                        (!currentLeagueCode && league.code === null);
                      return (
                        <NavLink
                          key={league.code || "all"}
                          to={league.code ? `/?league=${league.code}` : "/"}
                          onClick={() => setIsLeagueOpen(false)} // ЗАКРЫТИЕ ПРИ ВЫБОРЕ
                          className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${
                            isActive
                              ? "bg-red-600 text-white"
                              : "text-gray-400 hover:bg-gray-900 hover:text-white"
                          }`}
                        >
                          <div className="w-10 h-10 lg:w-12 lg:h-12 rounded-lg flex items-center justify-center flex-shrink-0 bg-white p-1.5">
                            {league.logo ? (
                              <img
                                src={league.logo}
                                alt=""
                                className="w-full h-full object-contain"
                              />
                            ) : (
                              <span className="text-[10px] font-black text-yellow-500">
                                ALL
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] lg:text-xs font-black uppercase truncate">
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
    </header>
  );
}

export default Header;
