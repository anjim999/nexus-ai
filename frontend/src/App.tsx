import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Documents from './pages/Documents';
import Agents from './pages/Agents';
import Reports from './pages/Reports';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="chat" element={<Chat />} />
          <Route path="documents" element={<Documents />} />
          <Route path="agents" element={<Agents />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
