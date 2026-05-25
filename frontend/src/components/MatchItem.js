import React from "react";
import { Link } from "react-router-dom";

const formatMatchTime = (utcDate) => {
  if (!utcDate) return { date: "", time: "" };
  try {
    const d = new Date(utcDate);
    return {
      date: d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" }),
      time: d.toLocaleTimeString("ru-RU", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
  } catch (e) {
    return { date: "", time: "" };
  }
};

const getOutcomeStyle = (outcome) => {
  if (outcome === "Win Home")
    return { text: "ПРОГНОЗ: П1", color: "bg-green-600 text-white" };
  if (outcome === "Win Away")
    return { text: "ПРОГНОЗ: П2", color: "bg-red-600 text-white" };
  if (outcome === "Draw")
    return { text: "ПРОГНОЗ: X", color: "bg-yellow-500 text-black" };
  return null;
};

function MatchItem({ match }) {
  if (!match || !match.homeTeam || !match.awayTeam) {
    return null;
  }

  const { date, time } = formatMatchTime(match.utcDate);
  const prediction = match.prediction
    ? getOutcomeStyle(match.prediction.outcome)
    : null;

  const TeamSection = ({ team }) => (
    <div className="flex flex-col items-center text-center w-2/5">
      <div className="h-16 w-16 mb-2 flex items-center justify-center">
        {team.logo_url ? (
          <img
            src={team.logo_url}
            alt=""
            className="h-full w-full object-contain drop-shadow-md"
          />
        ) : (
          <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center text-gray-500 font-bold">
            ?
          </div>
        )}
      </div>
      <span className="text-xs font-black text-white uppercase truncate w-full leading-tight">
        {team.name_ru || team.name}
      </span>
    </div>
  );

  return (
    <Link
      to={`/match/${match.id}`}
      className="block bg-gray-900 rounded-2xl shadow-2xl border border-gray-800 overflow-hidden transform hover:-translate-y-1 transition-all relative"
    >
      <div className="absolute top-0 left-0 w-1.5 h-full bg-red-600 opacity-80 shadow-[0_0_10px_red]"></div>
      <div className="p-6">
        <div className="flex justify-around items-center mb-6">
          <TeamSection team={match.homeTeam} />
          <div className="flex flex-col items-center px-2">
            <span className="text-[10px] font-black text-gray-500 uppercase mb-1">
              {date}
            </span>
            <span className="text-2xl font-black text-white tracking-tighter leading-none">
              {time}
            </span>
            <span className="text-[10px] font-black text-gray-800 italic mt-2">
              VS
            </span>
          </div>
          <TeamSection team={match.awayTeam} />
        </div>

        {match.status === "FINISHED" ? (
          <div className="bg-white/5 py-4 rounded-xl border border-white/10 text-center animate-in fade-in zoom-in duration-500">
            <span className="text-[9px] font-black text-yellow-500 uppercase tracking-[0.3em] block mb-1">
              Финальный счет
            </span>
            <span className="text-4xl font-black text-white italic tracking-tighter">
              {match.score?.home ?? 0} : {match.score?.away ?? 0}
            </span>
          </div>
        ) : prediction ? (
          <div className="bg-white/5 py-4 rounded-xl border border-white/10 text-center">
            <div className="flex flex-col gap-2 items-center">
              <span
                className={`px-5 py-1 text-[10px] uppercase font-black rounded-md ${prediction.color}`}
              >
                {prediction.text}
              </span>
              <span className="text-white text-lg font-black tracking-widest italic uppercase">
                СЧЕТ: {match.prediction.exact_score}
              </span>
            </div>
          </div>
        ) : (
          <div className="py-4 text-center">
            <span className="text-[10px] font-black text-gray-700 uppercase tracking-widest animate-pulse">
              Анализ нейросети...
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}

export default MatchItem;
