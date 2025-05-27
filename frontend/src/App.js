import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import MatchDetailPage from "./pages/MatchDetailPage";
import Header from "./components/Layout/Header";
import HistoryPage from "./pages/HistoryPage";
import TablesPage from "./pages/TablesPage";

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-color-bg text-color-text-white">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-8 pt-16">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/match/:matchId" element={<MatchDetailPage />} />
            <Route path="/history" element={<HistoryPage />} />{" "}
            <Route path="/tables" element={<TablesPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
