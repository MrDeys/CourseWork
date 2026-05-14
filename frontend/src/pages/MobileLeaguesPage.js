import React from "react";
import { useNavigate } from "react-router-dom";
import plLogo from "../assets/leagues/premier-league.png";
import blLogo from "../assets/leagues/bundesliga.png";
import saLogo from "../assets/leagues/serie-a.png";
import pdLogo from "../assets/leagues/la-liga.png";
import flLogo from "../assets/leagues/ligue-1.png";

const leagues = [
  { code: null, name: "Все чемпионаты", logo: null },
  { code: "Premier_League", name: "Premier League", logo: plLogo },
  { code: "La_Liga", name: "La Liga", logo: pdLogo },
  { code: "Serie_A", name: "Serie A", logo: saLogo },
  { code: "Bundesliga", name: "Bundesliga", logo: blLogo },
  { code: "Ligue_1", name: "Ligue 1", logo: flLogo },
];

function MobileLeaguesPage() {
  const navigate = useNavigate();

  return (
    <div className="py-6 space-y-6">
      <h1 className="text-2xl font-black uppercase italic text-center">
        Выбор лиги
      </h1>
      <div className="grid grid-cols-2 gap-4">
        {leagues.map((league) => (
          <button
            key={league.code || "all"}
            onClick={() =>
              navigate(league.code ? `/?league=${league.code}` : "/")
            }
            className="bg-gray-900 border border-gray-800 rounded-3xl p-6 flex flex-col items-center gap-3 active:scale-95 transition-all"
          >
            <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center p-2">
              {league.logo ? (
                <img src={league.logo} alt="" className="object-contain" />
              ) : (
                <span className="text-yellow-500 font-black">ALL</span>
              )}
            </div>
            <span className="text-[10px] font-black uppercase text-center">
              {league.name}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default MobileLeaguesPage;
