import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { getMatches } from "../api";

function MobileSearchPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [allTeams, setAllTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const data = await getMatches(null);
        const teamMap = new Map();

        data.forEach((m) => {
          [m.homeTeam, m.awayTeam].forEach((team) => {
            if (!team) return;

            if (!teamMap.has(team.id)) {
              teamMap.set(team.id, {
                id: team.id,
                name_ru: team.name_ru || "",
                name_en: team.name || "",
                displayName: team.name_ru || team.name,
                logo: team.logo_url,
              });
            }
          });
        });

        const sortedTeams = Array.from(teamMap.values()).sort((a, b) =>
          a.displayName.localeCompare(b.displayName),
        );
        setAllTeams(sortedTeams);
      } catch (e) {
        console.error("Search error", e);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
    window.scrollTo(0, 0);
  }, []);

  const filteredTeams = useMemo(() => {
    const query = searchTerm.toLowerCase().trim();
    if (!query) return [];

    return allTeams
      .filter(
        (t) =>
          t.name_ru.toLowerCase().includes(query) ||
          t.name_en.toLowerCase().includes(query),
      )
      .slice(0, 15);
  }, [searchTerm, allTeams]);

  return (
    <div className="py-4 pb-24 min-h-screen">
      <div className="sticky top-0 bg-color-bg pt-2 pb-4 z-10">
        <h1 className="text-xl font-black uppercase italic mb-4">
          Поиск команды
        </h1>
        <input
          autoFocus
          type="text"
          placeholder="Например: Manchester United"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-gray-900 border border-gray-800 rounded-2xl py-4 px-6 text-white focus:outline-none focus:border-red-600 transition-all font-bold shadow-2xl"
        />
      </div>

      {loading ? (
        <div className="text-center py-10 animate-pulse text-gray-600 font-black">
          ЗАГРУЗКА БАЗЫ...
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-2">
          {filteredTeams.map((team) => (
            <button
              key={team.id}
              onClick={() =>
                navigate(`/?search=${encodeURIComponent(team.displayName)}`)
              }
              className="flex items-center gap-4 bg-gray-900/40 p-4 rounded-2xl active:bg-red-600 transition-all border border-transparent active:border-white/10"
            >
              <img
                src={team.logo}
                alt=""
                className="w-10 h-10 object-contain"
              />
              <div className="flex flex-col items-start">
                <span className="text-sm font-black uppercase text-gray-200">
                  {team.displayName}
                </span>
                {searchTerm &&
                  team.name_en
                    .toLowerCase()
                    .includes(searchTerm.toLowerCase()) &&
                  team.name_ru && (
                    <span className="text-[10px] text-gray-500 font-bold uppercase">
                      {team.name_en}
                    </span>
                  )}
              </div>
            </button>
          ))}

          {searchTerm && filteredTeams.length === 0 && (
            <div className="text-center py-10 text-gray-600 font-bold uppercase tracking-widest">
              Ничего не найдено
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MobileSearchPage;
