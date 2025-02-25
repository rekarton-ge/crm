// src/components/documents/DocumentTable.jsx
import React, { useState } from 'react';
import { Table, Spin, Alert, Button, message } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

// Словарь для правильного склонения типов документов
const documentTypeNames = {
  upd: {
    single: 'УПД',
    multiple: 'УПД',
    genitive: 'УПД'
  },
  invoice: {
    single: 'счет',
    multiple: 'счета',
    genitive: 'счетов'
  },
  specification: {
    single: 'спецификация',
    multiple: 'спецификации',
    genitive: 'спецификаций'
  },
  contract: {
    single: 'договор',
    multiple: 'договора',
    genitive: 'договоров'
  },
  // Значение по умолчанию
  default: {
    single: 'документ',
    multiple: 'документа',
    genitive: 'документов'
  }
};

// Общий компонент таблицы документов
const DocumentTable = ({
  isLoading,
  error,
  errorMessage,
  data,
  columns,
  emptyMessage,
  onDelete,
  documentType = 'default'
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

    // Получаем правильные формы слова для текущего типа документа
    const types = documentTypeNames[documentType] || documentTypeNames.default;

    // Выбираем правильную форму в зависимости от количества
    const count = selectedRowKeys.length;
    const form = count === 1
      ? types.single
      : (count > 1 && count < 5
        ? types.multiple
        : types.genitive);

    try {
      const deletionPromises = selectedRowKeys.map(id => onDelete(id));
      await Promise.all(deletionPromises);

      message.success(`Удален${count === 1 ? '' : 'о'} ${count} ${form}`);
      setSelectedRowKeys([]); // Очищаем выбор после удаления
    } catch (error) {
      message.error(`Не удалось удалить ${types.genitive}`);
      console.error(error);
    }
  };

  // Если загрузка - показываем centered спиннер
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '200px'
      }}>
        <Spin size="large" />
      </div>
    );
  }

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

  return (
    <>
      {selectedRowKeys.length > 0 && (
        <div style={{
          marginBottom: 16,
          display: 'flex',
          alignItems: 'center',
          backgroundColor: '#f0f2f5',
          padding: '10px',
          borderRadius: '4px'
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
        dataSource={documents}
        columns={tableColumns}
        rowKey="id"
        rowSelection={{
          selectedRowKeys,
          onChange: onSelectChange,
        }}
        locale={{ emptyText: emptyMessage }}
        pagination={false}
      />
    </>
  );
};

export default DocumentTable;