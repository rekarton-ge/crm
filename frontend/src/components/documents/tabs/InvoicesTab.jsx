// src/components/documents/tabs/InvoicesTab.jsx
import React from 'react';
import { useGetInvoicesQuery, useDeleteInvoiceMutation } from '../../../api/documentsApi';
import DocumentTable from '../DocumentTable';

const InvoicesTab = () => {
  const {
    data: invoicesData,
    isLoading: isInvoicesLoading,
    error: invoicesError
  } = useGetInvoicesQuery();

  const [deleteInvoice] = useDeleteInvoiceMutation();

  const columns = [
    { key: 'number', title: 'Номер' },
    { key: 'date', title: 'Дата' },
    {
      key: 'client',
      title: 'Клиент',
      format: (client) => client?.name || '-'
    },
    {
      key: 'amount',
      title: 'Сумма',
      format: (amount) => amount ? `${amount.toLocaleString()} ₽` : '-'
    },
    {
      key: 'contract',
      title: 'Договор',
      format: (contract) => contract?.number || '-'
    },
    {
      key: 'specification',
      title: 'Спецификация',
      format: (specification) => specification?.number || '-'
    },
    { key: 'status', title: 'Статус' }
  ];

  return (
    <DocumentTable
      isLoading={isInvoicesLoading}
      error={invoicesError}
      errorMessage="Ошибка загрузки счетов"
      data={invoicesData}
      columns={columns}
      emptyMessage="Счета не найдены"
      onDelete={deleteInvoice}
      documentType="invoice"
    />
  );
};

export default InvoicesTab;