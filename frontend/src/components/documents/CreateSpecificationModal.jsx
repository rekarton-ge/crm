// src/components/documents/CreateSpecificationModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, DatePicker, Select, Upload, Button, message, InputNumber, Spin } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import { useGetClientsQuery } from '../../api/clientsApi';
import { useGetContractsQuery, useCreateSpecificationMutation, useExtractPDFDataMutation } from '../../api/documentsApi';
import locale from 'antd/es/date-picker/locale/ru_RU';
import dayjs from 'dayjs';

const { Option } = Select;
const { Dragger } = Upload;

const CreateSpecificationModal = ({ visible, onCancel }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState(null);

  const { data: clientsData, isLoading: isClientsLoading } = useGetClientsQuery({ page: 1, limit: 100 });
  const { data: contractsData, isLoading: isContractsLoading } = useGetContractsQuery();
  const [createSpecification, { isLoading: isCreating }] = useCreateSpecificationMutation();
  const [extractPDFData, { isLoading: extracting }] = useExtractPDFDataMutation();

  // Сбросить форму при закрытии
  useEffect(() => {
    if (!visible) {
      form.resetFields();
      setFileList([]);
      setSelectedClientId(null);
    }
  }, [visible, form]);

  // Фильтрация договоров по выбранному клиенту
  const filteredContracts = contractsData?.results?.filter(
    contract => selectedClientId ? contract.client === selectedClientId : true
  ) || [];

  const handleOk = async () => {
    try {
      const values = await form.validateFields();

      // Создаем FormData для отправки файла
      const formData = new FormData();
      formData.append('number', values.number);
      formData.append('date', values.date.format('YYYY-MM-DD'));
      formData.append('client', values.client);
      formData.append('contract', values.contract);

      if (values.total_amount) {
        formData.append('total_amount', values.total_amount);
      }

      // Добавляем файл, если он был загружен
      if (fileList.length > 0) {
        formData.append('file', fileList[0].originFileObj);
      }

      await createSpecification(formData).unwrap();
      message.success('Спецификация успешно создана');
      onCancel();
    } catch (error) {
      console.error('Failed:', error);
      message.error('Не удалось создать спецификацию');
    }
  };

  const handleExtractData = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const extractedData = await extractPDFData(formData).unwrap();

      // Заполняем форму извлеченными данными
      form.setFieldsValue({
        number: extractedData.number,
        date: extractedData.date ? dayjs(extractedData.date) : null,
        client: extractedData.client_id,
        contract: extractedData.contract_id,
        total_amount: extractedData.total_amount,
      });

      if (extractedData.client_id) {
        setSelectedClientId(extractedData.client_id);
      }

      message.success('Данные успешно извлечены из файла');
    } catch (error) {
      console.error('Failed to extract data:', error);
      message.error('Не удалось извлечь данные из файла');
    }
  };

  const beforeUpload = (file) => {
    // Проверка размера файла (например, до 5MB)
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('Файл должен быть меньше 5MB!');
      return false;
    }

    // Проверка типа файла
    const isPDF = file.type === 'application/pdf';
    if (!isPDF) {
      message.error('Можно загрузить только PDF файл!');
      return false;
    }

    handleExtractData(file);
    return false; // Отменяем автоматическую загрузку
  };

  const handleChange = (info) => {
    setFileList(info.fileList.slice(-1)); // Ограничиваем до одного файла
  };

  const onClientChange = (clientId) => {
    setSelectedClientId(clientId);
    form.setFieldValue('contract', undefined); // Сбрасываем выбранный договор
  };

  const draggerProps = {
    name: 'file',
    multiple: false,
    fileList,
    beforeUpload,
    onChange: handleChange,
    customRequest: ({ onSuccess }) => {
      setTimeout(() => {
        onSuccess("ok");
      }, 0);
    },
  };

  return (
    <Modal
      title="Создание спецификации"
      open={visible}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={isCreating || extracting}
      okText="Создать"
      cancelText="Отмена"
      width={700}
      destroyOnClose
    >
      <Form
        name="create_specification_form"
        form={form}
        layout="vertical"
      >
        <Dragger
          {...draggerProps}
          style={{ marginBottom: 24 }}
          disabled={extracting}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            {extracting ? 'Извлечение данных...' : 'Нажмите или перетащите PDF файл для загрузки'}
          </p>
          <p className="ant-upload-hint">
            Система автоматически извлечет данные из файла для заполнения формы
          </p>
        </Dragger>

        <Form.Item
          name="number"
          label="Номер спецификации"
          rules={[{ required: true, message: 'Пожалуйста, введите номер спецификации' }]}
        >
          <Input placeholder="Введите номер спецификации" />
        </Form.Item>

        <Form.Item
          name="date"
          label="Дата спецификации"
          rules={[{ required: true, message: 'Пожалуйста, выберите дату спецификации' }]}
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
            onChange={onClientChange}
          >
            {clientsData?.results?.map(client => (
              <Option key={client.id} value={client.id}>{client.name}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="contract"
          label="Договор"
          rules={[{ required: true, message: 'Пожалуйста, выберите договор' }]}
        >
          <Select
            placeholder="Выберите договор"
            loading={isContractsLoading}
            showSearch
            optionFilterProp="children"
            disabled={!selectedClientId}
          >
            {filteredContracts.map(contract => (
              <Option key={contract.id} value={contract.id}>
                {contract.number} - {contract.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="total_amount"
          label="Общая сумма"
          rules={[{ required: true, message: 'Пожалуйста, введите сумму' }]}
        >
          <InputNumber
            placeholder="Введите сумму"
            style={{ width: '100%' }}
            formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={value => value.replace(/\s/g, '')}
            precision={2}
            min={0}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateSpecificationModal;