// src/components/documents/DocumentTable.jsx
import React, { useState } from 'react';
import { Table, Spin, Alert, Button, message } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

// Общий компонент таблицы документов
const DocumentTable = ({
  isLoading,
  error,
  errorMessage,
  data,
  columns,
  emptyMessage,
  onDeleteMultiple,
  documentType
}) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  // Форматирование даты
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return format(new Date(dateString), 'dd.MM.yyyy', { locale: ru });
    } catch (e) {
      return dateString;
    }
  };

  // Обработчик выбора строк
  const onSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  // Обработчик удаления выбранных документов
  const handleDeleteSelected = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите документы для удаления');
      return;
    }

    try {
      await onDeleteMultiple(selectedRowKeys);
      message.success(`Удалено ${selectedRowKeys.length} документов`);
      setSelectedRowKeys([]); // Очищаем выбор после удаления
    } catch (error) {
      message.error('Не удалось удалить документы');
      console.error(error);
    }
  };

  if (error) return <Alert message={errorMessage} description={error.message} type="error" showIcon />;

  const documents = data?.results || [];

  // Преобразуем колонки для Ant Design Table
  const tableColumns = columns.map(column => ({
    title: column.title,
    dataIndex: column.key,
    key: column.key,
    render: (text, record) => {
      if (column.render) {
        return column.render(text, record);
      } else if (column.format) {
        return column.format(record[column.key], record);
      } else if (column.key === 'date') {
        return formatDate(text);
      } else {
        return text || '-';
      }
    }
  }));

  // Конфигурация выбора строк
  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
  };

return (
  <div>
    {selectedRowKeys.length > 0 && (
      <div style={{
        marginBottom: 10,
        display: 'flex',
        alignItems: 'center',

        padding: '3px',
        borderRadius: '5px'
      }}>
        <Button
          type="primary"
          danger
          icon={<DeleteOutlined />}
          onClick={handleDeleteSelected}
        >
          Удалить выбранные ({selectedRowKeys.length})
        </Button>
      </div>
    )}

      <Table
        rowSelection={rowSelection}
        columns={tableColumns}
        dataSource={documents}
        rowKey="id"
        loading={isLoading}
        locale={{ emptyText: emptyMessage }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `Всего: ${total}`,
          defaultPageSize: 10,
          pageSizeOptions: ['10', '20', '50']
        }}
      />
    </div>
  );
};

export default DocumentTable;