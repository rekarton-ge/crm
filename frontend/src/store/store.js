// src/store/store.js
import { configureStore } from '@reduxjs/toolkit';
import { clientsApi } from '../api/clientsApi';
import { documentsApi } from '../api/documentsApi'; // Добавляем импорт API документов

const store = configureStore({
    reducer: {
        [clientsApi.reducerPath]: clientsApi.reducer,
        [documentsApi.reducerPath]: documentsApi.reducer, // Добавляем reducer для документов
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(
            clientsApi.middleware,
            documentsApi.middleware // Добавляем middleware для документов
        ),
});

export default store;