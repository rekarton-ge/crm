// src/components/documents/tabs/SpecificationsTab.jsx
import React from 'react';
import { useGetSpecificationsQuery, useDeleteSpecificationMutation } from '../../../api/documentsApi';
import DocumentTable from '../DocumentTable';

const SpecificationsTab = () => {
  const {
    data: specificationsData,
    isLoading: isSpecificationsLoading,
    error: specificationsError
  } = useGetSpecificationsQuery();

  const [deleteSpecification] = useDeleteSpecificationMutation();

  const columns = [
    { key: 'number', title: 'Номер' },
    { key: 'date', title: 'Дата' },
    {
      key: 'contract',
      title: 'Договор',
      format: (contract) => contract?.number || '-'
    },
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
    { key: 'status', title: 'Статус' }
  ];

  return (
    <DocumentTable
      isLoading={isSpecificationsLoading}
      error={specificationsError}
      errorMessage="Ошибка загрузки спецификаций"
      data={specificationsData}
      columns={columns}
      emptyMessage="Спецификации не найдены"
      onDelete={deleteSpecification}
      documentType="specification"
    />
  );
};

export default SpecificationsTab;