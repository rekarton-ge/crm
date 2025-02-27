import { baseApi } from './baseApi';

export const documentsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // ===== КОНТРАКТЫ =====
    getContracts: builder.query({
      query: () => 'documents/contracts/',
      providesTags: (result) =>
        result
          ? [
              { type: 'Document', id: 'CONTRACTS' },
              ...result.results.map(({ id }) => ({ type: 'Document', id: `Contract-${id}` })),
            ]
          : [{ type: 'Document', id: 'CONTRACTS' }],
    }),

    getContractById: builder.query({
      query: (id) => `documents/contracts/${id}/`,
      providesTags: (result, error, id) => [{ type: 'Document', id: `Contract-${id}` }],
    }),

    createContract: builder.mutation({
      query: (data) => {
        // Проверяем, является ли data экземпляром FormData
        const isFormData = data instanceof FormData;

        return {
          url: 'documents/contracts/',
          method: 'POST',
          body: data,
          // Если передаем FormData, не устанавливаем заголовок Content-Type,
          // чтобы браузер автоматически установил правильный boundary
          headers: isFormData ? undefined : { 'Content-Type': 'application/json' },
          formData: isFormData,
        };
      },
      invalidatesTags: [{ type: 'Document', id: 'CONTRACTS' }],
    }),

    deleteContract: builder.mutation({
      query: (id) => ({
        url: `documents/contracts/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Document', id: 'CONTRACTS' },
        { type: 'Document', id: `Contract-${id}` }
      ],
    }),

    // ===== СПЕЦИФИКАЦИИ =====
    getSpecifications: builder.query({
      query: () => 'documents/specifications/',
      providesTags: (result) =>
        result
          ? [
              { type: 'Document', id: 'SPECIFICATIONS' },
              ...result.results.map(({ id }) => ({ type: 'Document', id: `Specification-${id}` })),
            ]
          : [{ type: 'Document', id: 'SPECIFICATIONS' }],
    }),

    getSpecificationById: builder.query({
      query: (id) => `documents/specifications/${id}/`,
      providesTags: (result, error, id) => [{ type: 'Document', id: `Specification-${id}` }],
    }),

    createSpecification: builder.mutation({
      query: (data) => {
        // Проверяем, является ли data экземпляром FormData
        const isFormData = data instanceof FormData;

        return {
          url: 'documents/specifications/',
          method: 'POST',
          body: data,
          // Если передаем FormData, не устанавливаем заголовок Content-Type
          headers: isFormData ? undefined : { 'Content-Type': 'application/json' },
          formData: isFormData,
        };
      },
      invalidatesTags: [{ type: 'Document', id: 'SPECIFICATIONS' }],
    }),

    deleteSpecification: builder.mutation({
      query: (id) => ({
        url: `documents/specifications/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Document', id: 'SPECIFICATIONS' },
        { type: 'Document', id: `Specification-${id}` }
      ],
    }),

    // ===== СЧЕТА =====
    getInvoices: builder.query({
      query: () => 'documents/invoices/',
      providesTags: (result) =>
        result
          ? [
              { type: 'Document', id: 'INVOICES' },
              ...result.results.map(({ id }) => ({ type: 'Document', id: `Invoice-${id}` })),
            ]
          : [{ type: 'Document', id: 'INVOICES' }],
    }),

    getInvoiceById: builder.query({
      query: (id) => `documents/invoices/${id}/`,
      providesTags: (result, error, id) => [{ type: 'Document', id: `Invoice-${id}` }],
    }),

    createInvoice: builder.mutation({
      query: (data) => {
        const isFormData = data instanceof FormData;

        return {
          url: 'documents/invoices/',
          method: 'POST',
          body: data,
          headers: isFormData ? undefined : { 'Content-Type': 'application/json' },
          formData: isFormData,
        };
      },
      invalidatesTags: [{ type: 'Document', id: 'INVOICES' }],
    }),

    deleteInvoice: builder.mutation({
      query: (id) => ({
        url: `documents/invoices/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Document', id: 'INVOICES' },
        { type: 'Document', id: `Invoice-${id}` }
      ],
    }),

    // ===== УПД =====
    getUPDs: builder.query({
      query: () => 'documents/upds/',
      providesTags: (result) =>
        result
          ? [
              { type: 'Document', id: 'UPDS' },
              ...result.results.map(({ id }) => ({ type: 'Document', id: `UPD-${id}` })),
            ]
          : [{ type: 'Document', id: 'UPDS' }],
    }),

    getUPDById: builder.query({
      query: (id) => `documents/upds/${id}/`,
      providesTags: (result, error, id) => [{ type: 'Document', id: `UPD-${id}` }],
    }),

    createUPD: builder.mutation({
      query: (data) => {
        const isFormData = data instanceof FormData;

        return {
          url: 'documents/upds/',
          method: 'POST',
          body: data,
          headers: isFormData ? undefined : { 'Content-Type': 'application/json' },
          formData: isFormData,
        };
      },
      invalidatesTags: [{ type: 'Document', id: 'UPDS' }],
    }),

    deleteUPD: builder.mutation({
      query: (id) => ({
        url: `documents/upds/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Document', id: 'UPDS' },
        { type: 'Document', id: `UPD-${id}` }
      ],
    }),

    // Новый эндпоинт для извлечения данных из PDF
    extractPDFData: builder.mutation({
      query: (formData) => ({
        url: 'documents/extract-pdf-data/',
        method: 'POST',
        body: formData,
        formData: true,
      }),
    }),

    // Добавляем алиас для getContractById
    getContract: builder.query({
      query: (id) => `documents/contracts/${id}/`,
      providesTags: (result, error, id) => [{ type: 'Document', id: `Contract-${id}` }],
    }),
  }),
});

// Хуки для использования в компонентах
export const {
  // Контракты
  useGetContractsQuery,
  useGetContractByIdQuery,
  useGetContractQuery, // Добавляем экспорт для нового хука
  useCreateContractMutation,
  useDeleteContractMutation,

  // Спецификации
  useGetSpecificationsQuery,
  useGetSpecificationByIdQuery,
  useCreateSpecificationMutation,
  useDeleteSpecificationMutation,

  // Счета
  useGetInvoicesQuery,
  useGetInvoiceByIdQuery,
  useCreateInvoiceMutation,
  useDeleteInvoiceMutation,

  // УПД
  useGetUPDsQuery,
  useGetUPDByIdQuery,
  useCreateUPDMutation,
  useDeleteUPDMutation,

  // Извлечение данных из PDF
  useExtractPDFDataMutation,
} = documentsApi;