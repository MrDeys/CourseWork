import React, { useState, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import MatchItem from "./MatchItem";

function MatchList({ matches, selectedLeague, orderedLeagues }) {
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get("search")?.toLowerCase() || "";

  // null означает режим "ВСЕ"
  const [selectedDate, setSelectedDate] = useState(null);

  // Возвращаем компактный набор дат: 1 день назад, сегодня и 5 дней вперед
  const dateOptions = useMemo(() => {
    const dates = [];
    for (let i = -1; i <= 5; i++) {
      const d = new Date();
      d.setDate(d.getDate() + i);
      dates.push({
        full: d.toISOString().split("T")[0],
        day: d.getDate(),
        weekday: d.toLocaleDateString("ru-RU", { weekday: "short" }),
      });
    }
    return dates;
  }, []);

  // --- ЛОГИКА ФИЛЬТРАЦИИ ---
  const filteredMatches = useMemo(() => {
    let result = matches.filter((m) => m && m.homeTeam && m.awayTeam);
    const nowISO = new Date().toISOString();

    // 1. ПОИСК (показываем всё: историю и будущее по конкретной команде)
    if (searchQuery) {
      return result.filter((m) => {
        const h_en = m.homeTeam.name?.toLowerCase() || "";
        const a_en = m.awayTeam.name?.toLowerCase() || "";
        const h_ru = m.homeTeam.name_ru?.toLowerCase() || "";
        const a_ru = m.awayTeam.name_ru?.toLowerCase() || "";
        return (
          h_en.includes(searchQuery) ||
          a_en.includes(searchQuery) ||
          h_ru.includes(searchQuery) ||
          a_ru.includes(searchQuery)
        );
      });
    }

    // 2. Если выбрана КОНКРЕТНАЯ ДАТА (кнопка или календарь)
    if (selectedDate) {
      let dateFiltered = result.filter(
        (m) => m.utcDate.substring(0, 10) === selectedDate,
      );
      if (selectedLeague) {
        dateFiltered = dateFiltered.filter((m) => m.league === selectedLeague);
      }
      return dateFiltered;
    }

    // 3. Режим "ВСЕ" (selectedDate === null)
    // Показываем только ПРЕДСТОЯЩИЕ матчи
    let upcoming = result.filter((m) => m.utcDate >= nowISO);
    if (selectedLeague) {
      upcoming = upcoming.filter((m) => m.league === selectedLeague);
    }
    return upcoming;
  }, [matches, selectedLeague, selectedDate, searchQuery]);

  // Группировка
  const groupedMatches = useMemo(() => {
    const groups = {};
    filteredMatches.forEach((match) => {
      const leagueCode = match.league;
      if (!groups[leagueCode]) {
        const leagueObj = orderedLeagues.find(
          (l) => l.code === leagueCode || l.name === leagueCode,
        );
        groups[leagueCode] = {
          name: leagueObj ? leagueObj.name : leagueCode,
          order: leagueObj ? orderedLeagues.indexOf(leagueObj) : 999,
          matches: [],
        };
      }
      groups[leagueCode].matches.push(match);
    });
    return Object.entries(groups).sort((a, b) => a[1].order - b[1].order);
  }, [filteredMatches, orderedLeagues]);

  const formatErrorDate = (dateStr) => {
    if (!dateStr) return "ближайшее время";
    const [y, m, d] = dateStr.split("-");
    return `${d}-${m}-${y}`;
  };

  return (
    <div className="w-full">
      {/* ПАНЕЛЬ ДАТ (Компактная, без скролла на десктопе) */}
      {!searchQuery && (
        <div className="flex items-center gap-1 md:gap-2 mb-10 mt-0 bg-gray-900/40 p-1.5 rounded-b-2xl border-x border-b border-gray-800 w-full overflow-x-auto no-scrollbar">
          <button
            onClick={() => setSelectedDate(null)}
            className={`flex-1 min-w-[50px] flex items-center justify-center h-14 rounded-xl font-black text-[9px] uppercase transition-all ${selectedDate === null ? "bg-red-600 text-white shadow-lg shadow-red-600/30" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
          >
            ВСЕ
          </button>

          {dateOptions.map((d) => (
            <button
              key={d.full}
              onClick={() => setSelectedDate(d.full)}
              className={`flex-1 min-w-[56px] flex flex-col items-center justify-center h-14 rounded-xl transition-all ${selectedDate === d.full ? "bg-red-600 text-white shadow-lg shadow-red-600/30" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
            >
              <span className="text-[8px] font-black uppercase mb-1 leading-none">
                {d.weekday}
              </span>
              <span className="text-base font-black leading-none">{d.day}</span>
            </button>
          ))}

          <div className="relative flex-shrink-0 ml-1">
            <input
              type="date"
              className="absolute inset-0 opacity-0 cursor-pointer z-10"
              onChange={(e) => setSelectedDate(e.target.value)}
            />
            <button
              className={`w-12 h-14 flex items-center justify-center rounded-xl transition-colors ${selectedDate && !dateOptions.find((o) => o.full === selectedDate) ? "bg-red-600 text-white shadow-lg" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* ВЫВОД МАТЧЕЙ */}
      {groupedMatches.length === 0 ? (
        <div className="text-center py-20 bg-gray-900/20 rounded-3xl border border-gray-800/50 px-6 animate-in fade-in duration-500">
          <h3 className="text-white font-black uppercase tracking-tighter text-lg mb-2">
            {searchQuery
              ? `Команда "${searchQuery}" не найдена`
              : `Предстоящих матчей на ${formatErrorDate(selectedDate)} не найдено`}
          </h3>
          <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest leading-relaxed">
            Попробуйте выбрать другой день в календаре <br /> или воспользуйтесь
            поиском.
          </p>
        </div>
      ) : (
        groupedMatches.map(([code, league]) => (
          <div key={code} className="mb-14">
            <div className="flex flex-col items-center mb-8">
              <h2 className="text-2xl font-black text-white uppercase tracking-tighter italic">
                {league.name}
              </h2>
              <div className="w-16 h-1 bg-red-600 mt-2 rounded-full opacity-40 shadow-[0_0_10px_red]"></div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6 px-2">
              {league.matches.map((match) => (
                <MatchItem key={match.id} match={match} />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default MatchList;
