// src/store/store.js
import { configureStore } from '@reduxjs/toolkit';
import { clientsApi } from '../api/clientsApi'; // Корректный путь импорта

const store = configureStore({
    reducer: {
        [clientsApi.reducerPath]: clientsApi.reducer,
        // Добавьте другие редюсеры здесь, если необходимо
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(clientsApi.middleware),
});

export default store; // Экспортируем store как default экспорт