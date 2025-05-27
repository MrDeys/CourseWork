import React from "react";
import { Link } from "react-router-dom";

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

const getOutcomeColor = (predict) => {
  if (predict === "H")
    return { text: "Прогноз: П1", colorClasses: "bg-green-600 text-white" };
  if (predict === "A")
    return {
      text: "Прогноз: П2",
      colorClasses: "bg-color-primary-red text-white",
    };
  if (predict === "D")
    return {
      text: "Прогноз: X",
      colorClasses: "bg-color-primary-yellow text-color-bg",
    };
  return null;
};

function MatchItem({ match }) {
  const predict = match.Predicted_Outcome
    ? getOutcomeColor(match.Predicted_Outcome)
    : null;

  return (
    <Link
      to={`/match/${match.id}`}
      className="block bg-card-bg-gradient rounded-lg shadow-xl border border-color-card-border overflow-hidden
                 transform hover:-translate-y-1 hover:shadow-card-hover transition-all duration-300 ease-in-out"
    >
      <div className="p-4 md:p-5 flex flex-col h-full relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-transparent via-color-primary-red to-transparent opacity-75"></div>
        <div className="pl-3">
          <div className="flex justify-around items-center mb-3">
            <div className="flex flex-col items-center text-center w-2/5">
              {match.homeTeam_crest && (
                <img
                  src={match.homeTeam_crest}
                  alt={match.homeTeam_name}
                  className="h-16 w-16 object-contain mb-1"
                />
              )}
              <span className="text-sm font-semibold text-color-text-white truncate w-full">
                {match.homeTeam_name}
              </span>
            </div>
            <span className="text-2xl font-bold text-color-text-second">
              VS
            </span>
            <div className="flex flex-col items-center text-center w-2/5">
              {match.awayTeam_crest && (
                <img
                  src={match.awayTeam_crest}
                  alt={match.awayTeam_name}
                  className="h-16 w-16 object-contain mb-1"
                />
              )}
              <span className="text-sm font-semibold text-color-text-white truncate w-full">
                {match.awayTeam_name}
              </span>
            </div>
          </div>

          {predict && (
            <div className="my-3 text-center">
              <span
                className={`px-4 py-1.5 text-xs font-bold rounded-full shadow-md ${predict.colorClasses}`}
              >
                {predict.text}
              </span>
            </div>
          )}

          {match.status === "FINISHED" && (
            <p className="text-center text-lg font-bold my-2 text-color-primary-yellow">
              {match.score_fullTime_home} - {match.score_fullTime_away}
            </p>
          )}

          {!predict && match.status !== "FINISHED" && (
            <div className="my-3 h-8"></div>
          )}

          <div className="mt-auto text-center text-xs text-color-text-second pt-3">
            {dateTime(match.utcDate)}
          </div>
        </div>
      </div>
    </Link>
  );
}

export default MatchItem;
