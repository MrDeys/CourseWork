import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import MatchList from "../components/MatchList";
import { getMatches } from "../api";
import OfflineScreen from "../components/Layout/OfflineScreen";

import plLogo from "../assets/leagues/premier-league.png";
import blLogo from "../assets/leagues/bundesliga.png";
import saLogo from "../assets/leagues/serie-a.png";
import pdLogo from "../assets/leagues/la-liga.png";
import flLogo from "../assets/leagues/ligue-1.png";

const SidebarLeagues = [
  { code: null, name: "ВСЕ МАТЧИ", shortName: "Все", logo: null },
  { code: "Premier_League", name: "Premier League", logo: plLogo },
  { code: "La_Liga", name: "La Liga", logo: pdLogo },
  { code: "Serie_A", name: "Serie A", logo: saLogo },
  { code: "Bundesliga", name: "Bundesliga", logo: blLogo },
  { code: "Ligue_1", name: "Ligue 1", logo: flLogo },
];

function HomePage() {
  const [allMatches, setAllMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [searchParams] = useSearchParams();
  const LeagueCode = searchParams.get("league");

  const fetchAllMatches = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await getMatches(LeagueCode);
      if (data && data.length > 0) {
        setAllMatches(data);
        setError(false);
      } else {
        setError(true);
      }
    } catch (err) {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [LeagueCode]);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
    fetchAllMatches();
  }, [fetchAllMatches]);

  return (
    <div className="max-w-6xl mx-auto px-4 min-h-screen">
      <section className="w-full py-4">
        {loading ? (
          <div className="flex flex-col justify-center items-center h-96">
            <div className="w-10 h-10 border-4 border-red-600 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em]">
              Neural Syncing...
            </p>
          </div>
        ) : error ? (
          <OfflineScreen onRetry={fetchAllMatches} />
        ) : (
          <MatchList
            matches={allMatches}
            selectedLeague={LeagueCode}
            orderedLeagues={SidebarLeagues}
          />
        )}
      </section>
    </div>
  );
}

export default HomePage;
