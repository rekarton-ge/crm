// src/components/documents/tabs/SpecificationsTab.jsx
import React, { useState } from 'react';
import { useGetSpecificationsQuery, useDeleteSpecificationMutation } from '../../../api/documentsApi';
import DocumentTable from '../DocumentTable';

const SpecificationsTab = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  const {
    data: specificationsData,
    isLoading: isSpecificationsLoading,
    error: specificationsError
  } = useGetSpecificationsQuery();

  const [deleteSpecification] = useDeleteSpecificationMutation();

  const columns = [
    {
      key: 'number',
      title: 'Номер',
      render: (value) => value || '-'
    },
    {
      key: 'date',
      title: 'Дата',
      render: (date) => date ? new Date(date).toLocaleDateString() : '-'
    },
    {
      key: 'contract',
      title: 'Договор',
      render: (_, record) => record.contract_number || '-'
    },
    {
      key: 'client',
      title: 'Клиент',
      render: (_, record) => record.client_name || '-'
    },
    {
      key: 'total_amount',
      title: 'Сумма',
      render: (amount) => amount
        ? `${Number(amount).toLocaleString()} ₽`
        : '-'
    }
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
      selectedRowKeys={selectedRowKeys}
      onSelectChange={setSelectedRowKeys}
      documentType="specification"
    />
  );
};

export default SpecificationsTab;