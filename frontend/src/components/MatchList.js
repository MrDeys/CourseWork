import React from "react";
import MatchItem from "./MatchItem";

function MatchList({ matches, selectedLeague, orderedLeagues }) {
  if (matches.length === 0) {
    return (
      <p className="text-center text-color-text-muted py-10">
        Матчи на ближайшую неделю не найдены.
      </p>
    );
  }

  let filterMatches = {};

  if (!selectedLeague) {
    matches.forEach((match) => {
      const leagueCode = match.competition_code;
      const leagueName = orderedLeagues.find((l) => l.code === leagueCode).name;

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
    const leagueCodes = new Set();

    orderedLeagues.forEach((league) => {
      if (league.code && filterMatches[league.code]) {
        filterLeagues.push(filterMatches[league.code]);
        leagueCodes.add(league.code);
      }
    });
  }

  return (
    <div>
      {!selectedLeague ? (
        filterLeagues.map((league) => (
          <div key={league.code} className="mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold mb-6 text-center text-color-primary-yellow uppercase tracking-wider relative">
              {league.name}
              <div className="absolute left-1/2 -translate-x-1/2 bottom-0 w-3/4 h-0.5 bg-gradient-to-r from-transparent via-color-primary-red to-transparent opacity-75"></div>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
              {league.matches.map((match) => (
                <MatchItem key={match.id} match={match} />
              ))}
            </div>
          </div>
        ))
      ) : (
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
