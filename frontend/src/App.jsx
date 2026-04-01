import { Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import AlertDetailPage from "./pages/AlertDetailPage";

export default function App() {
  return (
    <div className="container">
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/alerts/:id" element={<AlertDetailPage />} />
      </Routes>
    </div>
  );
}
