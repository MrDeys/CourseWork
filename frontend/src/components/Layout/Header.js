import React, { useState, useEffect, useRef } from "react";
import { Link, NavLink, useLocation, useSearchParams } from "react-router-dom";

const leagues = [
  { code: "PL", name: "Premier League" },
  { code: "PD", name: "La liga" },
  { code: "SA", name: "Serie A" },
  { code: "BL1", name: "Bundesliga" },
  { code: "FL1", name: "Ligue 1" },
];

function Header() {
  const [isDropdown, setIsDropdown] = useState(false);
  const dropdownRef = useRef(null);
  const location = useLocation();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    function сlickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdown(false);
      }
    }
    document.addEventListener("mousedown", сlickOutside);
    return () => document.removeEventListener("mousedown", сlickOutside);
  }, [dropdownRef]);

  useEffect(() => {
    setIsDropdown(false);
  }, [location.pathname, location.search]);

  const allButtonClasses =
    "px-4 py-2 rounded-full text-xs sm:text-sm font-semibold transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-color-surface";

  const allActiveButtonClasses =
    "bg-color-button-active-bg text-color-button-active-text shadow-red-button";

  const allInactiveButtonClasses =
    "bg-color-button-inactive-bg text-color-button-inactive-text hover:bg-color-button-hover-bg hover:text-color-button-hover-text hover:shadow-red-button";

  const isDropdownActive = isDropdown || !!searchParams.get("league");

  return (
    <header className="bg-color-surface shadow-md sticky top-0 z-50 w-full">
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-color-primary-red to-transparent opacity-60"></div>
      <div className="container mx-auto px-4 h-16 flex justify-between items-center relative">
        <Link to="/" className="hover:opacity-90 transition-opacity">
          <span className="text-2xl md:text-3xl font-extrabold text-gradient-neuro-title tracking-tight">
            NeuroPredict
          </span>
        </Link>
        <nav className="flex items-center space-x-1 sm:space-x-2 md:space-x-3">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `${allButtonClasses} ${
                (isActive && !location.search && location.pathname === "/") ||
                (isActive && location.pathname !== "/")
                  ? allActiveButtonClasses
                  : allInactiveButtonClasses
              }`
            }
          >
            Главная
          </NavLink>
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsDropdown((prev) => !prev)}
              className={`${allButtonClasses} ${
                isDropdownActive
                  ? allActiveButtonClasses
                  : allInactiveButtonClasses
              } flex items-center`}
            >
              Лиги
              <svg
                className={`w-3 h-3 ml-1.5 transform transition-transform ${
                  isDropdown ? "rotate-180" : ""
                }`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                  clipRule="evenodd"
                ></path>
              </svg>
            </button>
            {isDropdown && (
              <div className="absolute left-0 mt-2 w-56 bg-color-surface rounded-md shadow-xl z-30 py-1 border border-gray-700">
                {leagues.map((league) => (
                  <NavLink
                    key={league.code}
                    to={`/?league=${league.code}`}
                    className={`block px-4 py-2 text-sm w-full text-left transition-colors
                      ${
                        searchParams.get("league") === league.code
                          ? "bg-color-primary-red text-color-button-inactive-text"
                          : "text-color-button-inactive-text hover:bg-color-primary-red hover:text-color-primary-yellow"
                      }`}
                  >
                    {league.name}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
          <NavLink
            to="/tables"
            className={({ isActive }) =>
              `${allButtonClasses} ${
                isActive ? allActiveButtonClasses : allInactiveButtonClasses
              }`
            }
          >
            Турнирные таблицы
          </NavLink>

          <NavLink
            to="/history"
            className={({ isActive }) =>
              `${allButtonClasses} ${
                isActive ? allActiveButtonClasses : allInactiveButtonClasses
              }`
            }
          >
            История матчей
          </NavLink>
        </nav>

        <div className="w-0 sm:w-32 md:w-48 lg:w-[18rem] hidden sm:block"></div>
      </div>
    </header>
  );
}

export default Header;
