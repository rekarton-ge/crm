// src/components/documents/tabs/ContractsTab.jsx
import React from 'react';
import { useGetContractsQuery, useDeleteContractMutation } from '../../../api/documentsApi';
import { useGetClientQuery } from '../../../api/clientsApi';
import DocumentTable from '../DocumentTable';
import { message } from 'antd';

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

  // Функция для удаления множества документов
  const handleDeleteMultiple = async (ids) => {
    try {
      // Выполняем удаление всех выбранных документов
      const deletionPromises = ids.map(id => deleteContract(id));
      await Promise.all(deletionPromises);
      message.success(`Удалено ${ids.length} договоров`);
    } catch (error) {
      message.error('Не удалось удалить договоры');
      console.error(error);
    }
  };

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
      onDeleteMultiple={handleDeleteMultiple}
      documentType="contract"
    />
  );
};

export default ContractsTab;