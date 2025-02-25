// src/api/clientsApi.js
import { baseApi } from './baseApi';

export const clientsApi = baseApi.injectEndpoints({
    endpoints: (builder) => ({
        // Получить список клиентов с пагинацией и поиском
        getClients: builder.query({
            query: ({ page = 1, search = '' }) => `clients/?page=${page}&search=${search}`,
            providesTags: (result) =>
                result
                    ? [
                          { type: 'ClientList', id: 'LIST' },
                          ...result.results.map(({ id }) => ({ type: 'Client', id })),
                      ]
                    : [{ type: 'ClientList', id: 'LIST' }],
        }),
        // Получить данные конкретного клиента по ID
        getClient: builder.query({
            query: (id) => `clients/${id}/`,
            providesTags: (result, error, id) => [{ type: 'Client', id }],
        }),
        // Создать нового клиента
        createClient: builder.mutation({
            query: (client) => ({
                url: 'clients/',
                method: 'POST',
                body: client,
            }),
            invalidatesTags: [{ type: 'ClientList', id: 'LIST' }],
        }),
        // Обновить данные клиента
        updateClient: builder.mutation({
            query: ({ id, ...client }) => ({
                url: `clients/${id}/`,
                method: 'PUT',
                body: client,
            }),
            invalidatesTags: (result, error, { id }) => [
                { type: 'Client', id },
                { type: 'ClientList', id: 'LIST' },
            ],
        }),
        // Удалить клиента
        deleteClient: builder.mutation({
            query: (id) => ({
                url: `clients/${id}/`,
                method: 'DELETE',
            }),
            invalidatesTags: (result, error, id) => [
                { type: 'Client', id },
                { type: 'ClientList', id: 'LIST' },
            ],
        }),
        // Получить список групп клиентов
        getClientGroups: builder.query({
            query: () => 'client-groups/',
            transformResponse: (response) => response.results,
        }),
        // Получить список тегов клиентов
        getTags: builder.query({
            query: () => 'tags/',
            transformResponse: (response) => response.results,
        }),
    }),
});

// Экспортируем хуки для использования в компонентах
export const {
    useGetClientsQuery,
    useGetClientQuery,
    useCreateClientMutation,
    useUpdateClientMutation,
    useDeleteClientMutation,
    useGetClientGroupsQuery,
    useGetTagsQuery,
} = clientsApi;