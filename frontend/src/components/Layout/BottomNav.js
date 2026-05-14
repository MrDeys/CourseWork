import React from "react";
import { NavLink } from "react-router-dom";

const BottomNav = () => {
  const navItems = [
    {
      to: "/",
      label: "Матчи",
      icon: (
        <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      ),
    },
    {
      to: "/search",
      label: "Поиск",
      icon: <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />,
    },
    {
      to: "/compare",
      label: "Анализ",
      icon: (
        <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      ),
    },
    {
      to: "/leagues",
      label: "Лиги",
      icon: <path d="M4 6h16M4 12h16m-7 6h7" />,
    },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-gray-950/95 backdrop-blur-xl border-t border-white/5 px-4 py-3 z-[200] flex justify-between items-center shadow-2xl">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 flex-1 transition-all ${isActive ? "text-red-600 scale-110" : "text-gray-500"}`
          }
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            viewBox="0 0 24 24"
          >
            {item.icon}
          </svg>
          <span className="text-[8px] font-black uppercase tracking-widest">
            {item.label}
          </span>
        </NavLink>
      ))}
    </nav>
  );
};

export default BottomNav;
