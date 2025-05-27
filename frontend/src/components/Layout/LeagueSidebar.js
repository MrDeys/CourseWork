import React from "react";

function LeagueSidebar({ leagues, selectedLeague, onSelectLeague }) {
  return (
    <div className="bg-color-surface p-2 sm:p-3 rounded-lg shadow-md">
      <ul className="space-y-1.5 sm:space-y-2">
        {leagues.map((league) => {
          const isActive =
            selectedLeague === league.code ||
            (!selectedLeague && league.code === null);

          return (
            <li key={league.code || "all-leagues"}>
              <button
                onClick={() => onSelectLeague(league.code)}
                className={`
                  w-full flex flex-col items-center justify-center p-2 rounded-md
                  transition-colors duration-150 ease-in-out group
                  focus:outline-none
                `}
              >
                <div
                  className={`
                    w-14 h-14 sm:w-16 sm:h-16 mb-1 rounded-md
                    flex items-center justify-center overflow-hidden
                    transition-all duration-150 ease-in-out
                    border-2
                    ${
                      isActive
                        ? "bg-color-primary-red border-color-primary-red shadow-red-button"
                        : "bg-gray-700 border-gray-700 group-hover:border-color-primary-red"
                    }
                  `}
                >
                  {league.logo ? (
                    <img
                      src={league.logo}
                      alt={`${league.name} logo`}
                      className="w-full h-full object-contain p-1.5"
                    />
                  ) : (
                    <span
                      className={`text-lg sm:text-xl font-bold
                      ${"text-color-primary-yellow"}`}
                    >
                      {league.code === null ? "ALL" : league.code}
                    </span>
                  )}
                </div>
                <span
                  className={`text-xs text-center truncate w-full mt-1 px-1 transition-colors
                    ${
                      isActive
                        ? "text-color-primary-red font-semibold"
                        : "text-color-primary-yellow group-hover:text-color-yellow-bright"
                    }`}
                >
                  {league.name}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default LeagueSidebar;
