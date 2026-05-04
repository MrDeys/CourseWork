import React from "react";
import { Link } from "react-router-dom";

const dateTime = (utcDate) => {
  if (!utcDate) return "";
  const date = new Date(utcDate);
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getOutcomeColor = (outcome) => {
  if (outcome === "Win Home")
    return { text: "Прогноз: П1", colorClasses: "bg-green-600 text-white" };
  if (outcome === "Win Away")
    return {
      text: "Прогноз: П2",
      colorClasses: "bg-red-600 text-white",
    };
  if (outcome === "Draw")
    return {
      text: "Прогноз: X",
      colorClasses: "bg-yellow-500 text-black",
    };
  return null;
};

function MatchItem({ match }) {
  const predictionData = match.prediction
    ? getOutcomeColor(match.prediction.outcome)
    : null;

  // Внутренний компонент для отрисовки команды (лого или буква)
  const TeamSection = ({ team }) => {
    const [imgError, setImgError] = React.useState(false);

    return (
      <div className="flex flex-col items-center text-center w-2/5">
        <div className="h-16 w-16 mb-2 flex items-center justify-center">
          {team.logo && !imgError ? (
            <img
              src={team.logo}
              alt={team.name}
              className="h-full w-full object-contain drop-shadow-md"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="h-full w-full bg-gradient-to-br from-gray-700 to-gray-900 rounded-full flex items-center justify-center border border-gray-600 shadow-inner">
              <span className="text-xl font-bold text-gray-400">
                {team.name.substring(0, 1)}
              </span>
            </div>
          )}
        </div>
        <span className="text-sm font-bold text-white truncate w-full">
          {team.name}
        </span>
      </div>
    );
  };

  return (
    <Link
      to={`/match/${match.id}`}
      className="block bg-gray-900 rounded-lg shadow-xl border border-gray-800 overflow-hidden
                 transform hover:-translate-y-1 hover:border-gray-600 transition-all duration-300 ease-in-out"
    >
      <div className="p-4 md:p-5 flex flex-col h-full relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-red-600 opacity-75"></div>

        <div className="pl-3">
          {/* Секция команд */}
          <div className="flex justify-around items-center mb-3">
            <TeamSection team={match.homeTeam} />
            <span className="text-2xl font-black text-gray-700 italic">VS</span>
            <TeamSection team={match.awayTeam} />
          </div>

          {/* Секция прогноза */}
          {predictionData && (
            <div className="my-3 text-center bg-black/30 py-2 rounded-md border border-white/5">
              <div className="flex flex-col gap-1 items-center">
                <span
                  className={`px-4 py-1 text-[10px] uppercase font-black rounded-full shadow-sm ${predictionData.colorClasses}`}
                >
                  {predictionData.text}
                </span>
                <span className="text-gray-400 text-xs font-medium">
                  Счет:{" "}
                  <span className="text-white">
                    {match.prediction.exact_score}
                  </span>
                </span>
              </div>
            </div>
          )}

          {/* Результат (если матч завершен) */}
          {match.status === "FINISHED" && (
            <div className="text-center my-2">
              <span className="text-2xl font-black text-yellow-500 tracking-tighter">
                {match.score.homeTeam} : {match.score.awayTeam}
              </span>
            </div>
          )}

          {/* Заглушка если нет данных */}
          {!predictionData && match.status !== "FINISHED" && (
            <div className="my-3 h-10 flex items-center justify-center">
              <span className="text-gray-600 text-xs animate-pulse uppercase tracking-widest font-bold">
                Анализ данных...
              </span>
            </div>
          )}

          {/* Дата матча */}
          <div className="mt-auto text-center text-[9px] text-gray-500 pt-3 border-t border-gray-800 uppercase tracking-widest font-semibold">
            {dateTime(match.utcDate)}
          </div>
        </div>
      </div>
    </Link>
  );
}

export default MatchItem;
