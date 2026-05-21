import { Routes, Route } from 'react-router-dom';
import UploadResume from './pages/UploadResume';
import Interview from './pages/Interview';
import Report from './pages/Report';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadResume />} />
      <Route path="/interview/:sessionId" element={<Interview />} />
      <Route path="/report/:sessionId" element={<Report />} />
    </Routes>
  );
}
