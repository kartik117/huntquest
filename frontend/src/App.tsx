import { Navigate, Route, Routes } from 'react-router-dom';
import { JoinPage } from './pages/JoinPage';
import { MapPage } from './pages/MapPage';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/join" replace />} />
      <Route path="/join" element={<JoinPage />} />
      <Route path="/map" element={<MapPage />} />
    </Routes>
  );
}
