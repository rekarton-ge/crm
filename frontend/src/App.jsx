// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import store from './store/store'; // Предположим, что у вас настроен Redux store
import ClientList from './pages/ClientList';
import ClientForm from './pages/ClientForm';
import ClientCard from './pages/ClientCard'; // Импортируем ClientCard
import DocumentsPage from './pages/DocumentsPage';
import 'antd/dist/reset.css'; // Для Ant Design версии 5.x

const App = () => {
    return (
        <Provider store={store}>
            <Router>
                <Routes>
                    <Route path="/" element={<ClientList />} />
                    <Route path="/create" element={<ClientForm />} />
                    <Route path="/edit/:id" element={<ClientForm />} />
                    <Route path="/card/:id" element={<ClientCard />} /> {/* Новый маршрут */}
                    <Route path="/documents" element={<DocumentsPage />} />
                </Routes>
            </Router>
        </Provider>
    );
};

export default App;

