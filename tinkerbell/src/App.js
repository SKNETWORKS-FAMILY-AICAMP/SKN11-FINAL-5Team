import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Main from "./pages/user/main";
import SignUp from "./pages/user/signup";
import SignIn from "./pages/user/signin";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/signin" element={<SignIn />} />
      </Routes>
    </Router>
  );
}

export default App;
