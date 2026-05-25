import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import GraphPage from './pages/GraphPage';
import UploadPage from './pages/UploadPage';
import TablePage from './pages/TablePage';
import ConstructorPage from './pages/ConstructorPage';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-amber-50">
                <Navbar />
                <Routes>
                    <Route path="/" element={<GraphPage />} />
                    <Route path="/constructor" element={<ConstructorPage />} />
                    <Route path="/upload" element={<UploadPage />} />
                    <Route path="/table" element={<TablePage />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;