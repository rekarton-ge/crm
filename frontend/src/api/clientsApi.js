// src/api/clientsApi.js
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import axios from "axios";

export const clientsApi = createApi({
    reducerPath: 'clientsApi',
    baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8000/api/' }),
    tagTypes: ['Client', 'ClientList'],  // Добавляем тег для списка клиентов
    endpoints: (builder) => ({
        // Получить список клиентов с пагинацией и поиском
        getClients: builder.query({
            query: ({ page = 1, search = '' }) => `clients/?page=${page}&search=${search}`,
            providesTags: (result) =>
                result
                    ? [
                          { type: 'ClientList', id: 'LIST' },  // Тег для списка клиентов
                          ...result.results.map(({ id }) => ({ type: 'Client', id })),  // Теги для отдельных клиентов
                      ]
                    : [{ type: 'ClientList', id: 'LIST' }],
        }),
        // Получить данные конкретного клиента по ID
        getClient: builder.query({
            query: (id) => `clients/${id}/`,
            providesTags: (result, error, id) => [{ type: 'Client', id }],  // Тег для конкретного клиента
        }),
        // Создать нового клиента
        createClient: builder.mutation({
            query: (client) => ({
                url: 'clients/',
                method: 'POST',
                body: client,
            }),
            invalidatesTags: [{ type: 'ClientList', id: 'LIST' }],  // Инвалидируем тег списка клиентов после создания
        }),
        // Обновить данные клиента
        updateClient: builder.mutation({
            query: ({ id, ...client }) => ({
                url: `clients/${id}/`,
                method: 'PUT',
                body: client,
            }),
            invalidatesTags: (result, error, { id }) => [
                { type: 'Client', id },  // Инвалидируем тег конкретного клиента
                { type: 'ClientList', id: 'LIST' },  // Инвалидируем тег списка клиентов
            ],
        }),
        // Удалить клиента
        deleteClient: builder.mutation({
            query: (id) => ({
                url: `clients/${id}/`,
                method: 'DELETE',
            }),
            invalidatesTags: (result, error, id) => [
                { type: 'Client', id },  // Инвалидируем тег конкретного клиента
                { type: 'ClientList', id: 'LIST' },  // Инвалидируем тег списка клиентов
            ],
        }),
        // Получить список групп клиентов
        getClientGroups: builder.query({
            query: () => 'client-groups/',
            transformResponse: (response) => response.results,  // Преобразуем ответ в массив
        }),
        // Получить список тегов клиентов
        getTags: builder.query({
            query: () => 'tags/',
            transformResponse: (response) => response.results,  // Преобразуем ответ в массив
        }),
    }),
});

// Экспортируем хуки для использования в компонентах
export const {
    useGetClientsQuery,       // Хук для получения списка клиентов
    useGetClientQuery,        // Хук для получения данных клиента по ID
    useCreateClientMutation,  // Хук для создания клиента
    useUpdateClientMutation,  // Хук для обновления клиента
    useDeleteClientMutation,  // Хук для удаления клиента
    useGetClientGroupsQuery,  // Хук для получения списка групп
    useGetTagsQuery,          // Хук для получения списка тегов
} = clientsApi;

const API_URL = 'http://localhost:8000/api/clients/';

export const getClients = async () => {
  try {
    const response = await axios.get(API_URL);
    return response.data; // Возвращаем список клиентов
  } catch (error) {
    console.error('Ошибка при загрузке списка клиентов:', error);
    throw error;
  }
};