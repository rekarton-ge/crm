// src/components/documents/tabs/ContractsTab.jsx
import React from 'react';
import { useGetContractsQuery, useDeleteContractMutation } from '../../../api/documentsApi';
import { useGetClientQuery } from '../../../api/clientsApi';
import DocumentTable from '../DocumentTable';

// Компонент для отображения имени клиента
const ClientName = ({ clientId }) => {
  const { data: client } = useGetClientQuery(clientId, { skip: !clientId });
  return <span>{client?.name || '-'}</span>;
};

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
      // Используем собственный render вместо format
      render: (clientId) => <ClientName clientId={clientId} />
    },
    { key: 'name', title: 'Название' },
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