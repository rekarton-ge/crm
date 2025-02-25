// src/components/documents/tabs/ContractsTab.jsx
import React from 'react';
import { useGetContractsQuery, useDeleteContractMutation } from '../../../api/documentsApi';
import DocumentTable from '../DocumentTable';

const ContractsTab = () => {
  const {
    data: contractsData,
    isLoading: isContractsLoading,
    error: contractsError
  } = useGetContractsQuery();

  const [deleteContract] = useDeleteContractMutation();

  const columns = [
    { key: 'number', title: 'Номер' },
    { key: 'date', title: 'Дата' },
    {
      key: 'client',
      title: 'Клиент',
      format: (client) => client?.name || '-'
    },
    { key: 'title', title: 'Название' },
    { key: 'status', title: 'Статус' }
  ];

  return (
    <DocumentTable
      isLoading={isContractsLoading}
      error={contractsError}
      errorMessage="Ошибка загрузки договоров"
      data={contractsData}
      columns={columns}
      emptyMessage="Договоры не найдены"
      onDelete={deleteContract}
      documentType="contract"
    />
  );
};

export default ContractsTab;