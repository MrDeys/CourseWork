import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getMatchId } from "../api";

function MatchDetailPage() {
  const { matchId } = useParams();
  const [match, setMatch] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const isMatch = async () => {
      setLoading(true);
      const data = await getMatchId(matchId);
      setMatch(data);
      setLoading(false);
    };

    isMatch();
  }, [matchId]);

  const dateTime = (utcDate) => {
    let dateStr = utcDate;
    const date = new Date(dateStr);

    return date.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getWinner = (winner) => {
    if (winner === "HOME_TEAM") return "Хозяева";
    if (winner === "AWAY_TEAM") return "Гости";
    if (winner === "DRAW") return "Ничья";
    return "Неизвестно";
  };

  const sidebarTop = "top-16";
  const sidebarMaxHeight = "max-h-[calc(100vh_-_4rem_-_theme(spacing.8))]";

  const getPredictOutcome = (outcomeCode) => {
    if (outcomeCode === "H")
      return { text: "Победа хозяев (П1)", colorClass: "text-green-500" };
    if (outcomeCode === "A")
      return {
        text: "Победа гостей (П2)",
        colorClass: "text-color-primary-red",
      };
    if (outcomeCode === "D")
      return { text: "Ничья (X)", colorClass: "text-color-primary-yellow" };
    return { text: "Неизвестно", colorClass: "text-color-text-second" };
  };
  const predict = match?.Predicted_Outcome
    ? getPredictOutcome(match.Predicted_Outcome)
    : null;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-xl text-color-text-second animate-pulse">
          Загрузка деталей матча...
        </p>
      </div>
    );
  }

  if (!match) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-xl text-color-text-second">Матч не найден.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 lg:gap-8">
      <section className="w-full lg:flex-grow min-w-0">
        <div className="bg-color-surface rounded-lg shadow-lg p-6 md:p-8 mb-6 text-center">
          <div className="flex justify-around items-center">
            <div className="flex flex-col items-center w-1/3">
              {match.homeTeam_crest && (
                <img
                  src={match.homeTeam_crest}
                  alt={match.homeTeam_name}
                  className="h-24 w-24 md:h-32 md:w-32 object-contain mb-2"
                />
              )}
              <span className="text-lg md:text-xl font-bold text-color-text-white">
                {match.homeTeam_name}
              </span>
            </div>
            <span className="text-4xl md:text-5xl font-bold text-color-primary-red mx-4">
              VS
            </span>
            <div className="flex flex-col items-center w-1/3">
              {match.awayTeam_crest && (
                <img
                  src={match.awayTeam_crest}
                  alt={match.awayTeam_name}
                  className="h-24 w-24 md:h-32 md:w-32 object-contain mb-2"
                />
              )}
              <span className="text-lg md:text-xl font-bold text-color-text-white">
                {match.awayTeam_name}
              </span>
            </div>
          </div>
          <div className="text-sm md:text-base text-color-text-second mt-4">
            <p>{dateTime(match.utcDate)}</p>
            {match.matchday && <p>Тур: {match.matchday}</p>}
            <p>{match.competition_name}</p>
          </div>
        </div>
        {match.status === "FINISHED" && (
          <div className="bg-color-surface rounded-lg shadow-lg p-6 md:p-8 mb-6 text-center">
            <h3 className="text-xl font-bold text-color-primary-yellow mb-3">
              Результат матча
            </h3>
            <p className="text-3xl font-extrabold text-color-text-white mb-2">
              {match.score_fullTime_home} - {match.score_fullTime_away}
            </p>
            <p className="text-center text-lg font-bold mt-10">
              <span className="text-color-text-white">Победитель: </span>
              <span className={predict?.colorClass}>
                {getWinner(match.score_winner)}
              </span>
            </p>
          </div>
        )}

        {match.Predicted_Outcome && (
          <div className="bg-color-surface rounded-lg shadow-lg p-6 md:p-8 mb-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-transparent via-color-primary-red to-transparent opacity-75"></div>
            <div className="pl-3">
              <h3 className="text-xl font-bold text-color-primary-yellow mb-6 text-center">
                Прогноз и Вероятности
              </h3>
              <div className="w-full bg-gray-700 rounded-full h-3 mb-2 flex overflow-hidden shadow-inner">
                <div
                  className="bg-green-500 h-full transition-all duration-500"
                  style={{ width: `${(match.Prob_H * 100).toFixed(2)}%` }}
                ></div>
                <div
                  className="bg-color-primary-yellow h-full transition-all duration-500"
                  style={{ width: `${(match.Prob_D * 100).toFixed(2)}%` }}
                ></div>
                <div
                  className="bg-color-primary-red h-full transition-all duration-500"
                  style={{ width: `${(match.Prob_A * 100).toFixed(2)}%` }}
                ></div>
              </div>
              <div className="relative w-full h-0">
                <div
                  className="absolute top-0 text-sm font-bold text-green-500"
                  style={{
                    left: `calc(${match.Prob_H * 100}% / 2 - 2.2ch)`,
                  }}
                >
                  {match.Prob_H !== null
                    ? `${(match.Prob_H * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
                <div
                  className="absolute top-0 text-sm font-bold text-color-primary-yellow"
                  style={{
                    left: `calc(${(match.Prob_H * 100).toFixed(1)}% + ${(
                      match.Prob_D * 100
                    ).toFixed(1)}% / 2 - 2.2ch)`,
                  }}
                >
                  {match.Prob_D !== null
                    ? `${(match.Prob_D * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
                <div
                  className="absolute top-0 text-sm font-bold text-color-primary-red"
                  style={{
                    left: `calc(${(match.Prob_H * 100).toFixed(1)}% + ${(
                      match.Prob_D * 100
                    ).toFixed(1)}% + ${(match.Prob_A * 100).toFixed(
                      1
                    )}% / 2 - 2.2ch)`,
                  }}
                >
                  {match.Prob_A !== null
                    ? `${(match.Prob_A * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>
              <p className="text-center text-lg font-bold mt-10">
                <span className="text-color-text-white">
                  Пронзон от нейросети:{" "}
                </span>
                <span className={predict?.colorClass}>{predict?.text}</span>
              </p>
            </div>
          </div>
        )}

        <div className="bg-color-surface rounded-lg shadow-lg p-6 md:p-8 text-center">
          <h3 className="text-xl font-bold text-color-primary-yellow mb-3 text-center">
            Последние матчи команд
          </h3>
          <p className="text-color-text-second text-center">
            Функция в разработке.
          </p>
        </div>
      </section>

      <aside
        className={`w-full lg:w-72 xl:w-80 flex-shrink-0 hidden md:block lg:sticky ${sidebarTop} self-start ${sidebarMaxHeight} overflow-y-auto rounded-lg`}
      >
        <div className="bg-color-surface p-4 rounded-lg shadow-md min-h-[300px] flex flex-col text-center">
          {" "}
          <h3 className="text-xl font-semibold mb-3 text-color-primary-yellow">
            Турнирная таблица
          </h3>
          <p className="text-color-text-second flex-grow flex items-center justify-center">
            Функция в разработке.
          </p>
        </div>
      </aside>
    </div>
  );
}

export default MatchDetailPage;
