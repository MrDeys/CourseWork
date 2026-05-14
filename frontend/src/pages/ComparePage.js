import React, { useState, useEffect, useRef } from "react";
import { getMatches, getTeamComparison } from "../api";

// --- ВСПОМОГАТЕЛЬНЫЕ КОМПОНЕНТЫ ---

const ResultCircle = ({ res }) => {
  const colors = { W: "bg-green-500", D: "bg-yellow-500", L: "bg-red-600" };
  return (
    <span
      className={`${colors[res]} w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-black text-white shadow-lg`}
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
        <span className="text-3xl font-black text-white">
          {(parseFloat(h) || 0).toFixed(2)}
        </span>
        <span className="text-[10px] font-black text-white uppercase tracking-widest mb-2 opacity-60 text-center">
          {label}
        </span>
        <span className="text-3xl font-black text-white">
          {(parseFloat(a) || 0).toFixed(2)}
        </span>
      </div>
      <div className="h-3 w-full bg-gray-800 rounded-full flex overflow-hidden p-0.5 border border-gray-700">
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

// --- КОМПОНЕНТ ИСТОРИИ (С ПРЯТАНЬЕМ ТЕКСТА НА МОБИЛКЕ) ---
const HistoryList = ({ title, matches }) => (
  <div className="bg-gray-800/40 p-6 md:p-8 rounded-[32px] border border-white/5 h-full shadow-xl">
    <h3 className="text-xs font-black text-white uppercase tracking-[0.2em] mb-8 text-center">
      {title}
    </h3>
    <div className="space-y-4">
      {matches && matches.length > 0 ? (
        matches.map((m, i) => (
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
              {/* Скрываем название на мобилке */}
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
        ))
      ) : (
        <p className="text-sm text-gray-600 italic text-center py-6">
          Нет данных
        </p>
      )}
    </div>
  </div>
);

const getH2HResultStyle = (score, pastHomeId, focusTeamId) => {
  const [homeG, awayG] = score.split(":").map(Number);
  if (homeG === awayG)
    return "bg-yellow-500 text-black shadow-[0_0_15px_rgba(234,179,8,0.3)]";

  const isFocusTeamHomeInPast = pastHomeId === focusTeamId;

  if (isFocusTeamHomeInPast) {
    return homeG > awayG
      ? "bg-green-600 text-white shadow-[0_0_15px_rgba(22,163,74,0.4)]"
      : "bg-red-600 text-white shadow-[0_0_15px_rgba(220,38,38,0.4)]";
  } else {
    return awayG > homeG
      ? "bg-green-600 text-white shadow-[0_0_15px_rgba(22,163,74,0.4)]"
      : "bg-red-600 text-white shadow-[0_0_15px_rgba(220,38,38,0.4)]";
  }
};

function ComparePage() {
  const [allTeams, setAllTeams] = useState([]);
  const [team1, setTeam1] = useState("");
  const [team2, setTeam2] = useState("");
  const [suggestions1, setSuggestions1] = useState([]);
  const [suggestions2, setSuggestions2] = useState([]);
  const [showSugg1, setShowSugg1] = useState(false);
  const [showSugg2, setShowSugg2] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const input1Ref = useRef(null);
  const input2Ref = useRef(null);
  const container1Ref = useRef(null);
  const container2Ref = useRef(null);

  useEffect(() => {
    window.scrollTo(0, 0);
    const fetchTeams = async () => {
      try {
        const data = await getMatches(null);
        const teamMap = new Map();
        data.forEach((m) => {
          if (m.homeTeam) {
            teamMap.set(m.homeTeam.name, m.homeTeam.logo_url);
            if (m.homeTeam.name_ru)
              teamMap.set(m.homeTeam.name_ru, m.homeTeam.logo_url);
          }
          if (m.awayTeam) {
            teamMap.set(m.awayTeam.name, m.awayTeam.logo_url);
            if (m.awayTeam.name_ru)
              teamMap.set(m.awayTeam.name_ru, m.awayTeam.logo_url);
          }
        });
        const teamsArray = Array.from(teamMap.entries()).map(
          ([name, logo]) => ({ name, logo }),
        );
        setAllTeams(teamsArray.sort((a, b) => a.name.localeCompare(b.name)));
      } catch (e) {
        console.error("Error loading teams", e);
      }
    };
    fetchTeams();

    const handleClickOutside = (e) => {
      if (container1Ref.current && !container1Ref.current.contains(e.target))
        setShowSugg1(false);
      if (container2Ref.current && !container2Ref.current.contains(e.target))
        setShowSugg2(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCompare = async (t1 = team1, t2 = team2) => {
    if (!t1 || !t2) {
      setError("Введите названия обеих команд");
      return;
    }
    setLoading(true);
    setError("");
    setShowSugg1(false);
    setShowSugg2(false);
    const data = await getTeamComparison(t1, t2);
    if (data) setComparisonData(data);
    else setError("Команды не найдены");
    setLoading(false);
  };

  const handleInputChange = (val, setTeam, setSugg, setShow) => {
    setTeam(val);
    if (val.length > 0) {
      const filtered = allTeams
        .filter((t) => t.name.toLowerCase().includes(val.toLowerCase()))
        .slice(0, 10);
      setSugg(filtered);
      setShow(true);
    } else {
      setShow(false);
    }
  };

  const selectSuggestion = (teamObj, isSecondInput) => {
    if (isSecondInput) {
      setTeam2(teamObj.name);
      setShowSugg2(false);
      // Если первая команда еще не выбрана — перекидываем фокус на неё
      if (!team1) {
        input1Ref.current.focus();
      } else {
        handleCompare(team1, teamObj.name);
      }
    } else {
      setTeam1(teamObj.name);
      setShowSugg1(false);
      // Если вторая команда еще не выбрана — перекидываем фокус на неё
      if (!team2) {
        input2Ref.current.focus();
      } else {
        handleCompare(teamObj.name, team2);
      }
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 text-white font-sans">
      {/* 1. ПАНЕЛЬ ВЫБОРА КОМАНД */}
      <div className="bg-gray-900 p-8 rounded-[40px] border border-gray-800 shadow-2xl mb-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* ИНПУТ 1 (ХОЗЯЕВА) */}
          <div className="w-full md:w-2/5 relative" ref={container1Ref}>
            <input
              ref={input1Ref}
              type="text"
              value={team1}
              onChange={(e) =>
                handleInputChange(
                  e.target.value,
                  setTeam1,
                  setSuggestions1,
                  setShowSugg1,
                )
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  if (!team2) input2Ref.current.focus();
                  else handleCompare();
                }
              }}
              autoComplete="off"
              placeholder="Команда хозяев..."
              className="w-full bg-gray-950 border border-gray-800 rounded-2xl py-6 px-8 text-xl text-white focus:outline-none focus:border-red-600 transition-all font-black uppercase tracking-tight"
            />
            {showSugg1 && suggestions1.length > 0 && (
              <ul className="absolute top-full left-0 right-0 mt-3 bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl z-[100] overflow-hidden">
                {suggestions1.map((s, i) => (
                  <li
                    key={i}
                    onClick={() => selectSuggestion(s, false)}
                    className="flex items-center gap-5 px-6 py-5 hover:bg-red-600 cursor-pointer transition-all border-b border-gray-900 last:border-0 group"
                  >
                    <img
                      src={s.logo}
                      alt=""
                      className="w-10 h-10 object-contain group-hover:scale-110 transition-transform"
                    />
                    <span className="text-lg font-black uppercase">
                      {s.name}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* КНОПКА VS (Запуск анализа) */}
          <button
            onClick={() => handleCompare()}
            title="Сравнить команды"
            className="flex-shrink-0 w-16 h-16 bg-red-600 rounded-full flex items-center justify-center border-4 border-gray-900 text-white font-black italic shadow-xl z-10 uppercase hover:scale-110 active:scale-95 transition-all cursor-pointer group"
          >
            <span className="group-hover:animate-pulse">VS</span>
          </button>

          {/* ИНПУТ 2 (ГОСТИ) */}
          <div className="w-full md:w-2/5 relative" ref={container2Ref}>
            <input
              ref={input2Ref}
              type="text"
              value={team2}
              onChange={(e) =>
                handleInputChange(
                  e.target.value,
                  setTeam2,
                  setSuggestions2,
                  setShowSugg2,
                )
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  if (!team1) input1Ref.current.focus();
                  else handleCompare();
                }
              }}
              autoComplete="off"
              placeholder="Команда гостей..."
              className="w-full bg-gray-950 border border-gray-800 rounded-2xl py-6 px-8 text-xl text-white focus:outline-none focus:border-red-600 transition-all font-black uppercase tracking-tight"
            />
            {showSugg2 && suggestions2.length > 0 && (
              <ul className="absolute top-full left-0 right-0 mt-3 bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl z-[100] overflow-hidden">
                {suggestions2.map((s, i) => (
                  <li
                    key={i}
                    onClick={() => selectSuggestion(s, true)}
                    className="flex items-center gap-5 px-6 py-5 hover:bg-red-600 cursor-pointer transition-all border-b border-gray-900 last:border-0 group"
                  >
                    <img
                      src={s.logo}
                      alt=""
                      className="w-10 h-10 object-contain group-hover:scale-110 transition-transform"
                    />
                    <span className="text-lg font-black uppercase">
                      {s.name}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="text-center text-red-500 font-black uppercase tracking-widest mb-10 bg-red-600/10 py-5 rounded-2xl border border-red-600/20">
          {error}
        </div>
      )}
      {loading && (
        <div className="text-center py-20 text-red-600 font-black animate-pulse tracking-[0.4em]">
          ANALYZING...
        </div>
      )}

      {/* 2. РЕЗУЛЬТАТЫ СРАВНЕНИЯ */}
      {comparisonData && !loading && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 space-y-12">
          {/* ШАПКА КОМАНД */}
          <div className="flex flex-col md:flex-row justify-between items-center bg-gray-900 p-8 md:p-12 rounded-[40px] border border-gray-800 shadow-2xl relative overflow-hidden">
            <div className="flex flex-col items-center w-full md:w-2/5">
              <div className="text-[11px] font-black text-yellow-500 bg-gray-800 px-5 py-2 rounded-full mb-6 tracking-widest border border-gray-700 uppercase shadow-lg">
                ELO: {Math.round(comparisonData.team1.elo)}
              </div>
              <img
                src={comparisonData.team1.logo_url}
                className="h-40 w-40 object-contain mb-6 drop-shadow-2xl"
                alt=""
              />
              <h2 className="text-3xl font-black uppercase tracking-tighter text-center leading-none">
                {comparisonData.team1.name}
              </h2>
              <div className="flex gap-2 mt-6">
                {comparisonData.team1.stats.form.map((r, i) => (
                  <ResultCircle key={i} res={r} />
                ))}
              </div>
            </div>
            <span className="text-8xl font-black text-white opacity-5 italic my-10 md:my-0 uppercase tracking-tighter">
              VS
            </span>
            <div className="flex flex-col items-center w-full md:w-2/5">
              <div className="text-[11px] font-black text-yellow-500 bg-gray-800 px-5 py-2 rounded-full mb-6 tracking-widest border border-gray-700 uppercase shadow-lg">
                ELO: {Math.round(comparisonData.team2.elo)}
              </div>
              <img
                src={comparisonData.team2.logo_url}
                className="h-40 w-40 object-contain mb-6 drop-shadow-2xl"
                alt=""
              />
              <h2 className="text-3xl font-black uppercase tracking-tighter text-center leading-none">
                {comparisonData.team2.name}
              </h2>
              <div className="flex gap-2 mt-6">
                {comparisonData.team2.stats.form.map((r, i) => (
                  <ResultCircle key={i} res={r} />
                ))}
              </div>
            </div>
          </div>

          {/* ПРОГНОЗ НЕЙРОСЕТИ */}
          {comparisonData.prediction && (
            <div className="bg-gray-900 rounded-[40px] p-10 md:p-14 border border-gray-800 shadow-2xl relative overflow-hidden">
              <h2 className="text-xs font-black text-white opacity-40 uppercase tracking-[0.5em] mb-12 text-center">
                Neural Prediction Engine
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-10 items-stretch relative z-10">
                <div className="bg-black/40 p-8 rounded-[32px] border border-gray-800 flex flex-col justify-center">
                  <div className="flex justify-between mb-4 text-xs font-black uppercase text-white">
                    <span>П1: {comparisonData.prediction.prob_home}%</span>
                    <span>X: {comparisonData.prediction.prob_draw}%</span>
                    <span>П2: {comparisonData.prediction.prob_away}%</span>
                  </div>
                  <div className="h-6 w-full bg-gray-800 rounded-full overflow-hidden flex p-1 border border-gray-700">
                    <div
                      className="bg-green-500 h-full rounded-l-full"
                      style={{
                        width: `${comparisonData.prediction.prob_home}%`,
                      }}
                    ></div>
                    <div
                      className="bg-yellow-500 h-full"
                      style={{
                        width: `${comparisonData.prediction.prob_draw}%`,
                      }}
                    ></div>
                    <div
                      className="bg-red-600 h-full rounded-r-full"
                      style={{
                        width: `${comparisonData.prediction.prob_away}%`,
                      }}
                    ></div>
                  </div>
                </div>
                <div className="flex flex-col items-center justify-center p-8 bg-gray-800/30 rounded-[32px] border border-gray-800 text-center shadow-xl">
                  <span
                    className={`text-2xl font-black uppercase mb-4 tracking-widest ${comparisonData.prediction.outcome === "Win Home" ? "text-green-500" : comparisonData.prediction.outcome === "Win Away" ? "text-red-600" : "text-yellow-500"}`}
                  >
                    {comparisonData.prediction.outcome === "Win Home"
                      ? "Победа П1"
                      : comparisonData.prediction.outcome === "Win Away"
                        ? "Победа П2"
                        : "Ничья (X)"}
                  </span>
                  <span className="text-[10px] font-black text-white opacity-40 uppercase mb-4">
                    Прогноз счета
                  </span>
                  <span className="text-7xl font-black text-white italic tracking-tighter leading-none">
                    {comparisonData.prediction.exact_score}
                  </span>
                </div>
                <div className="bg-black/40 p-8 rounded-[32px] border border-gray-800 flex flex-col justify-center text-center">
                  <div className="flex justify-between mb-4 text-xs font-black uppercase text-white">
                    <span>
                      БОЛЬШЕ: {comparisonData.prediction.total_over_2_5}%
                    </span>
                    <span>
                      МЕНЬШЕ:{" "}
                      {(100 - comparisonData.prediction.total_over_2_5).toFixed(
                        1,
                      )}
                      %
                    </span>
                  </div>
                  <div className="h-6 w-full bg-gray-800 rounded-full overflow-hidden flex p-1 border border-gray-700 shadow-inner">
                    <div
                      className="bg-red-600 h-full rounded-l-full"
                      style={{
                        width: `${comparisonData.prediction.total_over_2_5}%`,
                      }}
                    ></div>
                    <div
                      className="bg-yellow-500 h-full rounded-r-full"
                      style={{
                        width: `${(100 - comparisonData.prediction.total_over_2_5).toFixed(1)}%`,
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* СТАТИСТИКА */}
          <div className="bg-gray-900 rounded-[40px] p-10 md:p-14 border border-gray-800 shadow-xl">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-16 md:gap-24">
              <div className="space-y-10">
                <div className="text-center mb-8">
                  <span className="inline-block bg-green-500/10 border border-green-500/30 text-green-500 text-[11px] font-black uppercase tracking-widest px-6 py-2 rounded-full">
                    Атакующий потенциал
                  </span>
                </div>
                <StatBar
                  label="В среднем забито"
                  h={comparisonData.team1.stats.gf}
                  a={comparisonData.team2.stats.gf}
                  color="bg-green-500"
                />
                <StatBar
                  label="Созданный xG"
                  h={comparisonData.team1.stats.xg_for}
                  a={comparisonData.team2.stats.xg_for}
                  color="bg-green-500"
                />
                <StatBar
                  label="Глубокие атаки"
                  h={comparisonData.team1.stats.deep}
                  a={comparisonData.team2.stats.deep}
                  color="bg-green-500"
                />
              </div>
              <div className="space-y-10">
                <div className="text-center mb-8">
                  <span className="inline-block bg-red-600/10 border border-red-600/30 text-red-500 text-[11px] font-black uppercase tracking-widest px-6 py-2 rounded-full">
                    Надежность обороны
                  </span>
                </div>
                <StatBar
                  label="В среднем пропущено"
                  h={comparisonData.team1.stats.ga}
                  a={comparisonData.team2.stats.ga}
                  reverse
                  color="bg-red-600"
                />
                <StatBar
                  label="Допущенный xG"
                  h={comparisonData.team1.stats.xg_against}
                  a={comparisonData.team2.stats.xg_against}
                  reverse
                  color="bg-red-600"
                />
                <StatBar
                  label="Прессинг (PPDA)"
                  h={comparisonData.team1.stats.ppda}
                  a={comparisonData.team2.stats.ppda}
                  reverse
                  color="bg-red-600"
                />
              </div>
            </div>
          </div>

          {/* ИСТОРИЯ */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <HistoryList
              title={`История: ${comparisonData.team1.name}`}
              matches={comparisonData.team1.history}
            />
            <HistoryList
              title={`История: ${comparisonData.team2.name}`}
              matches={comparisonData.team2.history}
            />
          </div>

          {/* ЛИЧНЫЕ ВСТРЕЧИ (H2H - ОБНОВЛЕНО ДЛЯ МОБИЛОК) */}
          <div className="bg-gray-900/60 p-6 md:p-12 rounded-[40px] border border-red-600/20 shadow-2xl">
            <h3 className="text-xs font-black text-red-600 uppercase tracking-[0.5em] mb-10 text-center">
              Очные встречи
            </h3>
            <div className="space-y-4 md:space-y-6">
              {comparisonData.h2h && comparisonData.h2h.length > 0 ? (
                comparisonData.h2h.map((m, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between bg-black/40 p-4 md:p-6 rounded-3xl border border-white/5 transition-all hover:border-white/10"
                  >
                    {/* Левая команда */}
                    <div className="flex-1 flex items-center justify-end gap-3 min-w-0">
                      <span className="text-sm md:text-lg font-black text-white uppercase truncate text-right hidden md:block">
                        {m.home}
                      </span>
                      <img
                        src={m.home_logo}
                        alt=""
                        className="w-8 h-8 md:w-9 md:h-9 object-contain flex-shrink-0"
                      />
                    </div>

                    {/* Центр */}
                    <div className="flex flex-col items-center gap-1 mx-3 md:mx-8 min-w-[90px] md:min-w-[120px]">
                      <span className="text-[9px] md:text-[11px] font-black text-white/40 uppercase tracking-[0.2em]">
                        {m.date}
                      </span>
                      <div
                        className={`px-4 py-1.5 md:px-6 md:py-2 rounded-xl text-lg md:text-2xl font-black italic tracking-tighter font-mono ${getH2HResultStyle(m.score, m.home_id, comparisonData.team1.id)}`}
                      >
                        {m.score}
                      </div>
                    </div>

                    {/* Правая команда */}
                    <div className="flex-1 flex items-center justify-start gap-3 min-w-0">
                      <img
                        src={m.away_logo}
                        alt=""
                        className="w-8 h-8 md:w-9 md:h-9 object-contain flex-shrink-0"
                      />
                      <span className="text-sm md:text-lg font-black text-white uppercase truncate text-left hidden md:block">
                        {m.away}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center py-10 text-gray-700 italic font-black uppercase tracking-widest">
                  История встреч не найдена
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComparePage;
