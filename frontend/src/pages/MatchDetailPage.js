import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getMatchId } from "../api";

const ResultCircle = ({ res }) => {
  const colors = { W: "bg-green-500", D: "bg-yellow-500", L: "bg-red-600" };
  return (
    <span
      className={`${colors[res]} w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black text-white shadow-lg`}
    >
      {res}
    </span>
  );
};

const StatBar = ({ label, h, a, reverse, color }) => {
  const isHomeBetter = reverse ? h < a : h > a;
  const total = (parseFloat(h) || 0) + (parseFloat(a) || 0) || 1;
  return (
    <div className="relative group">
      <div className="flex justify-between items-end mb-2">
        <span className="text-2xl font-black text-white">
          {(parseFloat(h) || 0).toFixed(2)}
        </span>
        <span className="text-[10px] font-black text-white uppercase tracking-widest mb-1 text-center opacity-60">
          {label}
        </span>
        <span className="text-2xl font-black text-white">
          {(parseFloat(a) || 0).toFixed(2)}
        </span>
      </div>
      <div className="h-2.5 w-full bg-gray-800 rounded-full flex overflow-hidden p-0.5 border border-gray-700">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${isHomeBetter ? color : "bg-gray-600"}`}
          style={{ width: `${((parseFloat(h) || 0) / total) * 100}%` }}
        ></div>
        <div
          className={`h-full rounded-full transition-all duration-1000 ${!isHomeBetter ? color : "bg-gray-600"}`}
          style={{ width: `${((parseFloat(a) || 0) / total) * 100}%` }}
        ></div>
      </div>
    </div>
  );
};

const HistoryList = ({ title, matches }) => (
  <div className="bg-gray-800/40 p-6 md:p-8 rounded-[32px] border border-white/5 h-full shadow-xl">
    <h3 className="text-xs font-black text-white uppercase tracking-[0.2em] mb-8 text-center">
      {title}
    </h3>
    <div className="space-y-4">
      {matches?.map((m, i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-3 bg-black/20 p-4 md:p-5 rounded-2xl border border-white/5"
        >
          <div
            className={`text-[9px] font-black px-2 py-1 rounded-lg border flex-shrink-0 ${m.is_home ? "bg-blue-500/10 text-blue-400 border-blue-500/20" : "bg-purple-500/10 text-purple-400 border-purple-500/20"}`}
          >
            {m.is_home ? "ДОМА" : "ГОСТИ"}
          </div>
          <div className="flex items-center gap-3 flex-grow min-w-0">
            <img
              src={m.opponent_logo}
              alt=""
              className="w-8 h-8 md:w-9 md:h-9 object-contain flex-shrink-0"
            />
            <span className="text-sm md:text-base font-black text-white truncate hidden md:block">
              {m.opponent}
            </span>
          </div>
          <div className="flex items-center gap-3 md:gap-5 flex-shrink-0">
            <span className="text-base md:text-lg font-black text-white font-mono italic">
              {m.score}
            </span>
            <span
              className={`w-8 h-8 md:w-9 md:h-9 rounded-xl flex items-center justify-center text-[10px] md:text-xs font-black shadow-lg ${m.res === "W" ? "bg-green-500 text-white" : m.res === "L" ? "bg-red-600 text-white" : "bg-yellow-500 text-black"}`}
            >
              {m.res}
            </span>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const getH2HResultStyle = (score, pastHomeId, currentHomeId) => {
  const [homeG, awayG] = score.split(":").map(Number);
  if (homeG === awayG)
    return "bg-yellow-500 text-black shadow-[0_0_15px_rgba(234,179,8,0.3)]";

  const wasCurrentHomeTeamHomeInPast = pastHomeId === currentHomeId;

  if (wasCurrentHomeTeamHomeInPast) {
    return homeG > awayG
      ? "bg-green-600 text-white shadow-[0_0_15px_rgba(22,163,74,0.4)]"
      : "bg-red-600 text-white shadow-[0_0_15px_rgba(220,38,38,0.4)]";
  } else {
    return awayG > homeG
      ? "bg-green-600 text-white shadow-[0_0_15px_rgba(22,163,74,0.4)]"
      : "bg-red-600 text-white shadow-[0_0_15px_rgba(220,38,38,0.4)]";
  }
};

function MatchDetailPage() {
  const { matchId } = useParams();
  const [match, setMatch] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    window.scrollTo(0, 0);
    const fetchData = async () => {
      setLoading(true);
      const data = await getMatchId(matchId);
      setMatch(data);
      setLoading(false);
    };
    fetchData();
  }, [matchId]);

  if (loading)
    return (
      <div className="h-screen flex items-center justify-center bg-gray-950 text-white font-black animate-pulse uppercase tracking-[0.5em]">
        System Analyzing...
      </div>
    );

  if (!match)
    return (
      <div className="text-center p-20 text-white font-black">
        Матч не найден
      </div>
    );

  const predStyle = match.prediction
    ? match.prediction.outcome === "Win Home"
      ? { text: "Победа П1", color: "text-green-500" }
      : match.prediction.outcome === "Win Away"
        ? { text: "Победа П2", color: "text-red-600" }
        : { text: "Ничья (X)", color: "text-yellow-500" }
    : null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 text-white font-sans space-y-10">
      <div className="bg-gray-900 p-8 md:p-12 rounded-[40px] border border-gray-800 shadow-2xl flex flex-col md:flex-row justify-between items-center relative overflow-hidden">
        <div className="flex flex-col items-center w-full md:w-2/5">
          <div className="text-[11px] font-black text-yellow-500 bg-gray-800 px-4 py-1.5 rounded-full mb-4 tracking-widest border border-gray-700">
            ELO: {Math.round(match.homeTeam.elo)}
          </div>
          <img
            src={match.homeTeam.logo_url}
            className="h-28 w-28 md:h-40 md:w-40 object-contain mb-4 drop-shadow-2xl"
            alt=""
          />
          <h1 className="text-2xl md:text-3xl font-black uppercase tracking-tighter text-center">
            {match.homeTeam.name_ru || match.homeTeam.name}
          </h1>
          <div className="flex gap-1.5 mt-4">
            {match.homeTeam.stats_last_5?.form.map((r, i) => (
              <ResultCircle key={i} res={r} />
            ))}
          </div>
        </div>

        <div className="my-10 md:my-0 text-center flex flex-col items-center justify-center min-w-[150px]">
          {match.status === "FINISHED" ? (
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-black text-yellow-500 uppercase tracking-[0.3em] mb-3">
                Завершено
              </span>
              <div className="text-5xl md:text-6xl font-black text-white bg-white/5 px-8 py-4 rounded-[32px] border border-white/10 shadow-2xl tracking-tighter italic">
                {match.score.home} : {match.score.away}
              </div>
            </div>
          ) : (
            <>
              <span className="text-6xl font-black text-white opacity-10 italic mb-4">
                VS
              </span>
              <div className="text-sm font-bold text-white tracking-widest uppercase mb-1">
                {new Date(match.utcDate).toLocaleDateString("ru-RU")}
              </div>
              <div className="text-3xl font-black text-white tracking-tight">
                {new Date(match.utcDate).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </>
          )}
        </div>

        <div className="flex flex-col items-center w-full md:w-2/5">
          <div className="text-[11px] font-black text-yellow-500 bg-gray-800 px-4 py-1.5 rounded-full mb-4 tracking-widest border border-gray-700">
            ELO: {Math.round(match.awayTeam.elo)}
          </div>
          <img
            src={match.awayTeam.logo_url}
            className="h-28 w-28 md:h-40 md:w-40 object-contain mb-4 drop-shadow-2xl"
            alt=""
          />
          <h1 className="text-2xl md:text-3xl font-black uppercase tracking-tighter text-center">
            {match.awayTeam.name_ru || match.awayTeam.name}
          </h1>
          <div className="flex gap-1.5 mt-4">
            {match.awayTeam.stats_last_5?.form.map((r, i) => (
              <ResultCircle key={i} res={r} />
            ))}
          </div>
        </div>
      </div>

      {match.prediction && (
        <div className="bg-gray-900 rounded-[32px] p-8 md:p-12 border border-gray-800 shadow-2xl">
          <h2 className="text-sm font-black text-white uppercase tracking-[0.3em] mb-10 text-center">
            Прогноз Нейросети
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch relative">
            <div className="bg-black/40 p-6 rounded-3xl border border-gray-800 flex flex-col justify-center">
              <h3 className="text-[11px] font-black text-white/50 uppercase tracking-widest mb-4 text-center">
                Вероятность исхода
              </h3>
              <div className="flex justify-between mb-3 text-xs font-black uppercase tracking-widest text-white/70">
                <span>П1: {match.prediction.prob_home}%</span>
                <span>X: {match.prediction.prob_draw}%</span>
                <span>П2: {match.prediction.prob_away}%</span>
              </div>
              <div className="h-5 w-full bg-gray-800 rounded-full overflow-hidden flex p-0.5 border border-gray-700">
                <div
                  className="bg-green-500 h-full"
                  style={{ width: `${match.prediction.prob_home}%` }}
                ></div>
                <div
                  className="bg-yellow-500 h-full"
                  style={{ width: `${match.prediction.prob_draw}%` }}
                ></div>
                <div
                  className="bg-red-600 h-full"
                  style={{ width: `${match.prediction.prob_away}%` }}
                ></div>
              </div>
            </div>

            <div className="flex flex-col items-center justify-center p-6 bg-gray-800/30 rounded-3xl border border-gray-800 text-center">
              <span
                className={`text-xl font-black uppercase mb-3 ${predStyle.color}`}
              >
                {predStyle.text}
              </span>
              <span className="text-[10px] font-black text-white opacity-40 uppercase mb-2">
                Счет
              </span>
              <span className="text-5xl font-black text-white italic tracking-tighter">
                {match.prediction.exact_score}
              </span>
            </div>

            <div className="bg-black/40 p-6 rounded-3xl border border-gray-800 flex flex-col justify-center">
              <h3 className="text-[11px] font-black text-white/50 uppercase tracking-widest mb-4 text-center">
                Больше или меньше 2.5 голов
              </h3>
              <div className="flex justify-between mb-3 text-xs font-black uppercase tracking-widest text-white/70">
                <span>БОЛЬШЕ: {match.prediction.total_over_2_5}%</span>
                <span>
                  МЕНЬШЕ: {(100 - match.prediction.total_over_2_5).toFixed(1)}%
                </span>
              </div>
              <div className="h-5 w-full bg-gray-800 rounded-full overflow-hidden flex p-0.5 border border-gray-700">
                <div
                  className="bg-red-600 h-full"
                  style={{ width: `${match.prediction.total_over_2_5}%` }}
                ></div>
                <div
                  className="bg-yellow-500 h-full"
                  style={{
                    width: `${(100 - match.prediction.total_over_2_5).toFixed(1)}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-gray-900 rounded-[32px] p-8 md:p-12 border border-gray-800 shadow-xl">
        <h2 className="text-sm font-black text-white uppercase tracking-[0.3em] mb-12 text-center">
          Анализ формы
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-20">
          <div className="space-y-8">
            <div className="text-center mb-6">
              <span className="inline-block bg-green-500/10 border border-green-500/30 text-green-500 text-[11px] font-black uppercase tracking-widest px-6 py-2 rounded-full">
                Атака
              </span>
            </div>
            <StatBar
              label="В среднем забито"
              h={match.homeTeam.stats_last_5.gf}
              a={match.awayTeam.stats_last_5.gf}
              color="bg-green-500"
            />
            <StatBar
              label="Созданный xG"
              h={match.homeTeam.stats_last_5.xg_for}
              a={match.awayTeam.stats_last_5.xg_for}
              color="bg-green-500"
            />
            <StatBar
              label="Глубокие атаки"
              h={match.homeTeam.stats_last_5.deep}
              a={match.awayTeam.stats_last_5.deep}
              color="bg-green-500"
            />
          </div>
          <div className="space-y-8">
            <div className="text-center mb-6">
              <span className="inline-block bg-red-600/10 border border-red-600/30 text-red-500 text-[11px] font-black uppercase tracking-widest px-6 py-2 rounded-full">
                Оборона
              </span>
            </div>
            <StatBar
              label="В среднем пропущено"
              h={match.homeTeam.stats_last_5.ga}
              a={match.awayTeam.stats_last_5.ga}
              reverse
              color="bg-red-600"
            />
            <StatBar
              label="Допущенный xG"
              h={match.homeTeam.stats_last_5.xg_against}
              a={match.awayTeam.stats_last_5.xg_against}
              reverse
              color="bg-red-600"
            />
            <StatBar
              label="Прессинг (PPDA)"
              h={match.homeTeam.stats_last_5.ppda}
              a={match.awayTeam.stats_last_5.ppda}
              reverse
              color="bg-red-600"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <HistoryList
          title={`История: ${match.homeTeam.name_ru || match.homeTeam.name}`}
          matches={match.homeTeam.history}
        />
        <HistoryList
          title={`История: ${match.awayTeam.name_ru || match.awayTeam.name}`}
          matches={match.awayTeam.history}
        />
      </div>

      <div className="bg-gray-900/60 p-6 md:p-12 rounded-[40px] border border-red-600/20 shadow-2xl">
        <h3 className="text-xs font-black text-red-600 uppercase tracking-[0.5em] mb-10 text-center">
          Очные встречи
        </h3>
        <div className="space-y-4">
          {match.h2h?.map((m, i) => (
            <div
              key={i}
              className="flex items-center justify-between bg-black/40 p-4 md:p-5 rounded-2xl border border-white/5 transition-all hover:border-white/10"
            >
              <div className="flex-1 flex items-center justify-end gap-3 min-w-0">
                <span className="text-sm md:text-base font-black uppercase truncate text-white hidden md:block text-right">
                  {m.home}
                </span>
                <img
                  src={m.home_logo}
                  alt=""
                  className="w-8 h-8 md:w-9 md:h-9 object-contain flex-shrink-0"
                />
              </div>

              <div className="flex flex-col items-center gap-1 mx-3 md:mx-10 min-w-[90px] md:min-w-[110px]">
                <span className="text-[9px] md:text-[10px] font-black text-white/40 uppercase">
                  {m.date}
                </span>
                <div
                  className={`px-4 py-1.5 md:px-5 md:py-1.5 rounded-xl text-lg md:text-xl font-black italic tracking-tighter ${getH2HResultStyle(m.score, m.home_id, match.homeTeam.id)}`}
                >
                  {m.score}
                </div>
              </div>

              <div className="flex-1 flex items-center justify-start gap-3 min-w-0">
                <img
                  src={m.away_logo}
                  alt=""
                  className="w-8 h-8 md:w-9 md:h-9 object-contain flex-shrink-0"
                />
                <span className="text-sm md:text-base font-black uppercase truncate text-white hidden md:block text-left">
                  {m.away}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MatchDetailPage;
