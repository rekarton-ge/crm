// src/components/documents/CreateContractModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, DatePicker, Select, Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useGetClientsQuery } from '../../api/clientsApi';
import { useCreateContractMutation } from '../../api/documentsApi';
import locale from 'antd/es/date-picker/locale/ru_RU';

const { Option } = Select;

const CreateContractModal = ({ visible, onCancel }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState([]);
  const { data: clientsData, isLoading: isClientsLoading } = useGetClientsQuery({ page: 1, limit: 100 });
  const [createContract, { isLoading: isCreating }] = useCreateContractMutation();

  // Сбросить форму при закрытии
  useEffect(() => {
    if (!visible) {
      form.resetFields();
      setFileList([]);
    }
  }, [visible, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();

      // Создаем FormData для отправки файла
      const formData = new FormData();
      formData.append('number', values.number);
      formData.append('name', values.name);
      formData.append('date', values.date.format('YYYY-MM-DD'));
      formData.append('client', values.client);
      formData.append('status', values.status);

      // Добавляем файл, если он был загружен
      if (fileList.length > 0) {
        formData.append('file', fileList[0].originFileObj);
      }

      await createContract(formData).unwrap();
      message.success('Договор успешно создан');
      onCancel();
    } catch (error) {
      console.error('Failed:', error);
      message.error('Не удалось создать договор');
    }
  };

  const beforeUpload = (file) => {
    // Проверка размера файла (например, до 5MB)
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('Файл должен быть меньше 5MB!');
    }
    return false; // Отменяем автоматическую загрузку
  };

  const handleChange = ({ fileList }) => {
    setFileList(fileList);
  };

  return (
    <Modal
      title="Создание договора"
      open={visible}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={isCreating}
      okText="Создать"
      cancelText="Отмена"
      destroyOnClose  // Добавлено для полного размонтирования
      forceRender    // Принудительный рендер
    >
      <Form
        name="create_contract_form"  // Добавлено уникальное имя формы
        form={form}
        layout="vertical"
        initialValues={{
          status: 'Не подписан'
        }}
      >
        <Form.Item
          name="number"
          label="Номер договора"
          rules={[{ required: true, message: 'Пожалуйста, введите номер договора' }]}
        >
          <Input placeholder="Введите номер договора" />
        </Form.Item>

        <Form.Item
          name="name"
          label="Имя договора"
          rules={[{ required: true, message: 'Пожалуйста, введите имя договора' }]}
        >
          <Input placeholder="Введите имя договора" />
        </Form.Item>

        <Form.Item
          name="date"
          label="Дата договора"
          rules={[{ required: true, message: 'Пожалуйста, выберите дату договора' }]}
        >
          <DatePicker locale={locale} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="client"
          label="Клиент"
          rules={[{ required: true, message: 'Пожалуйста, выберите клиента' }]}
        >
          <Select
            placeholder="Выберите клиента"
            loading={isClientsLoading}
            showSearch
            optionFilterProp="children"
          >
            {clientsData?.results?.map(client => (
              <Option key={client.id} value={client.id}>{client.name}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="status"
          label="Статус"
          rules={[{ required: true, message: 'Пожалуйста, выберите статус' }]}
        >
          <Select placeholder="Выберите статус">
            <Option value="Подписан">Подписан</Option>
            <Option value="Не подписан">Не подписан</Option>
            <Option value="На согласовании">На согласовании</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="file"
          label="Файл договора"
        >
          <Upload
            beforeUpload={beforeUpload}
            fileList={fileList}
            onChange={handleChange}
            maxCount={1}
          >
            <Button icon={<UploadOutlined />}>Выбрать файл</Button>
          </Upload>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateContractModal;