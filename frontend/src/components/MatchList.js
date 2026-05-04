import React from "react";
import MatchItem from "./MatchItem";

function MatchList({ matches, selectedLeague, orderedLeagues }) {
  if (!matches || matches.length === 0) {
    return <p className="text-center text-gray-500 py-10">Матчи не найдены.</p>;
  }

  // Группировка матчей по лигам (если выбрано "ВСЕ")
  let filterMatches = {};

  if (!selectedLeague) {
    matches.forEach((match) => {
      // ИСПРАВЛЕНО: используем match.league вместо match.competition_code
      const leagueCode = match.league;
      const leagueObj = orderedLeagues.find((l) => l.code === leagueCode);
      const leagueName = leagueObj ? leagueObj.name : leagueCode;

      if (!filterMatches[leagueCode]) {
        filterMatches[leagueCode] = {
          name: leagueName,
          code: leagueCode,
          matches: [],
        };
      }
      filterMatches[leagueCode].matches.push(match);
    });
  }

  let filterLeagues = [];

  if (!selectedLeague) {
    orderedLeagues.forEach((league) => {
      // Собираем только те лиги, в которых есть матчи прямо сейчас
      if (league.code && filterMatches[league.code]) {
        filterLeagues.push(filterMatches[league.code]);
      }
    });
  }

  return (
    <div>
      {!selectedLeague ? (
        // Вид "ВСЕ": выводим заголовки лиг и их матчи
        filterLeagues.map((league) => (
          <div key={league.code} className="mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold mb-6 text-center text-yellow-500 uppercase tracking-wider relative">
              {league.name}
              <div className="absolute left-1/2 -translate-x-1/2 bottom-0 w-3/4 h-0.5 bg-red-600 opacity-75"></div>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
              {league.matches.map((match) => (
                <MatchItem key={match.id} match={match} />
              ))}
            </div>
          </div>
        ))
      ) : (
        // Вид конкретной лиги: просто сетка матчей
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
          {matches.map((match) => (
            <MatchItem key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  );
}

export default MatchList;
