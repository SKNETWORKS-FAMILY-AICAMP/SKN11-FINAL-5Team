import logo from './logo.svg';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import MainPage from "./pages/chat/MainPage"
import ChatPage from "./pages/chat/ChatPage"
import ScenarioPage from './pages/chat/ScenarioPage';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/scenario" element={<ScenarioPage />} />
      </Routes>
    </Router>
  );
}

export default App;
