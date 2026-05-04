import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import MatchList from "../components/MatchList";
import { getMatches } from "../api";
import LeagueSidebar from "../components/Layout/LeagueSidebar";

import plLogo from "../assets/leagues/premier-league.png";
import blLogo from "../assets/leagues/bundesliga.png";
import saLogo from "../assets/leagues/serie-a.png";
import pdLogo from "../assets/leagues/la-liga.png";
import flLogo from "../assets/leagues/ligue-1.png";

// ИСПРАВЛЕНО: Коды (code) теперь должны СТРОГО совпадать с именами в БД (Premier_League и т.д.)
const SidebarLeagues = [
  { code: null, name: "ВСЕ", shortName: "Все", logo: null },
  { code: "Premier_League", name: "Premier League", logo: plLogo },
  { code: "La_Liga", name: "La liga", logo: pdLogo },
  { code: "Serie_A", name: "Serie A", logo: saLogo },
  { code: "Bundesliga", name: "Bundesliga", logo: blLogo },
  { code: "Ligue_1", name: "Ligue 1", logo: flLogo },
];

function HomePage() {
  const [allMatches, setAllMatches] = useState([]);
  const [displayMatches, setDisplayMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  const [searchParams, setSearchParams] = useSearchParams();
  const LeagueCode = searchParams.get("league");

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
  }, [LeagueCode]);

  useEffect(() => {
    const fetchAllMatches = async () => {
      setLoading(true);
      const data = await getMatches(null);
      console.log("Полученные данные из API:", data); // Проверка в консоли F12
      setAllMatches(data);
      setLoading(false);
    };
    fetchAllMatches();
  }, []);

  useEffect(() => {
    let filterMatches = allMatches;

    // ИСПРАВЛЕНО: поле теперь называется league, а не competition_code
    if (LeagueCode) {
      filterMatches = filterMatches.filter(
        (match) => match.league === LeagueCode,
      );
    }

    // ИСПРАВЛЕНО: Для отладки пока отключим жесткий фильтр по датам,
    // чтобы увидеть, приходят ли данные вообще.
    // Если всё заработает - вернешь фильтр на нужный диапазон.
    const Filter = [...filterMatches];

    Filter.sort((a, b) => new Date(a.utcDate) - new Date(b.utcDate));
    setDisplayMatches(Filter);
  }, [allMatches, LeagueCode, loading]);

  const LeagueSelect = (lCode) => {
    setSearchParams(lCode ? { league: lCode } : {});
  };

  const currentLeagueTitle = LeagueCode
    ? SidebarLeagues.find((l) => l.code === LeagueCode)
    : { name: "Все матчи" };

  const pageTitle = currentLeagueTitle ? currentLeagueTitle.name : "Все матчи";

  return (
    <div className="flex flex-col lg:flex-row gap-6 lg:gap-8">
      <aside className="w-full lg:w-60 xl:w-64 flex-shrink-0">
        <LeagueSidebar
          leagues={SidebarLeagues}
          selectedLeague={LeagueCode}
          onSelectLeague={LeagueSelect}
        />
      </aside>

      <section className="w-full lg:flex-grow min-w-0">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6 text-center text-yellow-500 uppercase tracking-wider">
          {pageTitle}
        </h1>
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <p className="text-xl animate-pulse">Загрузка матчей...</p>
          </div>
        ) : displayMatches.length === 0 ? (
          <div className="text-center p-10 bg-gray-800 rounded-lg">
            <p className="text-gray-400">
              Матчи не найдены в базе данных или не сгенерированы прогнозы.
            </p>
          </div>
        ) : (
          <MatchList
            matches={displayMatches}
            selectedLeague={LeagueCode}
            orderedLeagues={SidebarLeagues}
          />
        )}
      </section>
    </div>
  );
}

export default HomePage;
