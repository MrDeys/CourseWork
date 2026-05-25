import React, { useEffect } from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import HomePage from "./pages/HomePage";
import MatchDetailPage from "./pages/MatchDetailPage";
import Header from "./components/Layout/Header";
import ComparePage from "./pages/ComparePage";
import BottomNav from "./components/Layout/BottomNav";
import MobileLeaguesPage from "./pages/MobileLeaguesPage";
import MobileSearchPage from "./pages/MobileSearchPage";

const ScrollToTop = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
};

function App() {
  return (
    <Router>
      <ScrollToTop />
      <div className="flex flex-col min-h-screen bg-color-bg text-color-text-white pb-24 md:pb-0 relative">
        <Header />
        <main className="flex-grow container mx-auto px-4 pt-4 md:pt-4">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/match/:matchId" element={<MatchDetailPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/leagues" element={<MobileLeaguesPage />} />
            <Route path="/search" element={<MobileSearchPage />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </Router>
  );
}

export default App;
