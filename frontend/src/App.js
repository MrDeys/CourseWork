import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import MatchDetailPage from "./pages/MatchDetailPage";
import Header from "./components/Layout/Header";
import ComparePage from "./pages/ComparePage";

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-color-bg text-color-text-white">
        <Header />
        <main className="flex-grow container mx-auto px-4 pt-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/match/:matchId" element={<MatchDetailPage />} />
            <Route path="/compare" element={<ComparePage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
