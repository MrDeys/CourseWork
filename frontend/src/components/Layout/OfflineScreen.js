import React from "react";

const OfflineScreen = ({ onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center animate-in fade-in duration-700">
      <div className="w-24 h-24 bg-red-600/10 rounded-full flex items-center justify-center mb-6 border border-red-600/20">
        <svg
          className="w-12 h-12 text-red-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h2 className="text-xl font-black uppercase italic mb-2">
        Сервер недоступен
      </h2>
      <p className="text-gray-500 text-xs font-bold uppercase tracking-widest mb-8 leading-relaxed">
        Убедитесь, что ваш компьютер запущен <br /> и находится в одной сети с
        телефоном
      </p>
      <button
        onClick={onRetry}
        className="bg-red-600 text-white px-10 py-4 rounded-2xl font-black uppercase text-[10px] tracking-[0.2em] shadow-lg shadow-red-600/30 active:scale-95 transition-all"
      >
        Повторить попытку
      </button>
    </div>
  );
};

export default OfflineScreen;
