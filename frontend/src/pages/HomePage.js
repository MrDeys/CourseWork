import React, { useState, useEffect } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import MatchList from "../components/MatchList";
import { getMatches } from "../api";
import LeagueSidebar from "../components/Layout/LeagueSidebar";

import plLogo from "../assets/leagues/premier-league.png";
import blLogo from "../assets/leagues/bundesliga.png";
import saLogo from "../assets/leagues/serie-a.png";
import pdLogo from "../assets/leagues/la-liga.png";
import flLogo from "../assets/leagues/ligue-1.png";

const SidebarLeagues = [
  { code: null, name: "ВСЕ", shortName: "Все", logo: null },
  { code: "PL", name: "Premier League", logo: plLogo },
  { code: "PD", name: "La liga", logo: pdLogo },
  { code: "SA", name: "Serie A", logo: saLogo },
  { code: "BL1", name: "Bundesliga", logo: blLogo },
  { code: "FL1", name: "Ligue 1", logo: flLogo },
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
      setAllMatches(data);
      setLoading(false);
    };
    fetchAllMatches();
  }, []);

  useEffect(() => {
    let filterMatches = allMatches;

    if (LeagueCode) {
      filterMatches = filterMatches.filter(
        (match) => match.competition_code === LeagueCode
      );
    }

    // const now = new Date(); // Реальное время.
    const now = new Date("2025-05-01T00:00:00Z"); // Тестовая дата для отладки.
    const todayStart = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate()
    );
    const fourWeek = new Date(now.getTime() + 28 * 24 * 60 * 60 * 1000);
    fourWeek.setHours(23, 59, 59);

    const Filter = filterMatches.filter((match) => {
      const matchDate = new Date(match.utcDate);
      return matchDate >= todayStart && matchDate <= fourWeek;
    });

    Filter.sort((a, b) => new Date(a.utcDate) - new Date(b.utcDate));

    setDisplayMatches(Filter);
  }, [allMatches, LeagueCode, loading]);

  const LeagueSelect = (lCode) => {
    setSearchParams(lCode ? { league: lCode } : {});
  };

  const currentLeagueTitle = LeagueCode
    ? SidebarLeagues.find((l) => l.code === LeagueCode)
    : { name: "Все матчи" };

  const pageTitle = currentLeagueTitle.name;

  const sidebarTop = "top-16";
  const sidebarMaxHeight = "max-h-[calc(100vh_-_4rem_-_theme(spacing.8))]";

  return (
    <div className="flex flex-col lg:flex-row gap-6 lg:gap-8">
      <aside
        className={`
          w-full lg:w-60 xl:w-64 flex-shrink-0
          mb-6 lg:mb-0
          lg:sticky ${sidebarTop} self-start
          ${sidebarMaxHeight} overflow-y-auto
          rounded-lg
        `}
      >
        <LeagueSidebar
          leagues={SidebarLeagues}
          selectedLeague={LeagueCode}
          onSelectLeague={LeagueSelect}
        />
      </aside>

      <section className="w-full lg:flex-grow min-w-0">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6 text-center text-color-primary-yellow uppercase tracking-wider">
          {pageTitle}
        </h1>
        {loading && displayMatches.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <p className="text-xl text-color-text-second animate-pulse">
              Загрузка матчей...
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

      <aside
        className={`w-full lg:w-72 xl:w-80 flex-shrink-0 hidden md:block lg:sticky ${sidebarTop} self-start ${sidebarMaxHeight} overflow-y-auto rounded-lg`}
      >
        <div className="bg-color-surface p-4 rounded-lg shadow-md min-h-[300px] flex flex-col">
          <h3 className="text-xl font-semibold mb-3 text-color-primary-yellow">
            Турнирная таблица
          </h3>
          <p className="text-color-text-second flex-grow flex items-center justify-center text-center">
            Функция в разработке.
          </p>
        </div>
      </aside>
    </div>
  );
}

export default HomePage;
