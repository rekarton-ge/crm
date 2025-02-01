import React, { useEffect, useState } from "react";
import {
  Table, Spin, Tabs, Button, message, Input, Select, DatePicker, Modal,
  Form, Upload, Popconfirm, Dropdown, Menu
} from "antd";
import {
  PlusOutlined, UploadOutlined, DeleteOutlined, DownOutlined
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import {
  getContracts, createContract, deleteContract,
  getSpecifications, createSpecification, deleteSpecification,
  getInvoices, createInvoice, deleteInvoice,
  getUPDs, createUPD, deleteUPD
} from "../api/documentsApi";
import { getClients } from "../api/clientsApi";

const { Option } = Select;

const DocumentsPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState([]);
  const [specifications, setSpecifications] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [upds, setUPDs] = useState([]);
  const [clients, setClients] = useState([]);
  const [modalType, setModalType] = useState(null);
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [selectedDeleteType, setSelectedDeleteType] = useState(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [contractsData, specsData, invoicesData, updsData, clientsData] = await Promise.all([
        getContracts(),
        getSpecifications(),
        getInvoices(),
        getUPDs(),
        getClients()
      ]);

      setContracts(contractsData?.results || contractsData || []);
      setSpecifications(specsData?.results || specsData || []);
      setInvoices(invoicesData?.results || invoicesData || []);
      setUPDs(updsData?.results || updsData || []);
      setClients(clientsData?.results || clientsData || []);
    } catch (error) {
      message.error("Ошибка загрузки данных");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const formData = new FormData();

      // Общие поля для всех документов
      formData.append("number", values.number);
      formData.append("client", values.client);
      formData.append("date", values.date.format("YYYY-MM-DD"));

      // Условные поля
      if (values.name) formData.append("name", values.name);
      if (values.amount) formData.append("amount", values.amount);
      if (values.status) formData.append("status", values.status);

      // Прикрепление файла
      if (fileList.length > 0) {
        formData.append("file", fileList[0].originFileObj);
      }

      // Выбор API для создания документа
      let apiFunction;
      switch (modalType) {
        case "contract":
          apiFunction = createContract;
          break;
        case "specification":
          apiFunction = createSpecification;
          break;
        case "invoice":
          apiFunction = createInvoice;
          break;
        case "upd":
          apiFunction = createUPD;
          break;
        default:
          throw new Error("Неизвестный тип документа");
      }

      await apiFunction(formData);
      message.success("Документ успешно создан");

      // Сброс состояния
      fetchAllData();
      setModalType(null);
      form.resetFields();
      setFileList([]);
    } catch (error) {
      message.error("Ошибка при создании документа");
      console.error(error);
    }
  };

  const handleDeleteSelected = async () => {
    try {
      let deleteFunction;
      switch (selectedDeleteType) {
        case "contracts":
          deleteFunction = deleteContract;
          break;
        case "specifications":
          deleteFunction = deleteSpecification;
          break;
        case "invoices":
          deleteFunction = deleteInvoice;
          break;
        case "upds":
          deleteFunction = deleteUPD;
          break;
        default:
          throw new Error("Неизвестный тип для удаления");
      }

      await Promise.all(selectedRowKeys.map((id) => deleteFunction(id)));
      message.success("Выбранные элементы удалены");

      setSelectedRowKeys([]);
      fetchAllData();
    } catch (error) {
      message.error("Ошибка при удалении");
      console.error(error);
    }
  };

  const getDocumentTypeLabel = (type) => {
    const labels = {
      contract: "договора",
      specification: "спецификации",
      invoice: "счёта",
      upd: "УПД",
    };
    return labels[type] || "документа";
  };

  const menu = (
    <Menu onClick={(e) => setModalType(e.key)}>
      <Menu.Item key="contract">Создать договор</Menu.Item>
      <Menu.Item key="specification">Создать спецификацию</Menu.Item>
      <Menu.Item key="invoice">Создать счет</Menu.Item>
      <Menu.Item key="upd">Создать УПД</Menu.Item>
    </Menu>
  );

  if (loading) {
    return <Spin size="large" />;
  }

  return (
    <div style={{ padding: "24px" }}>
      <h1>Документы</h1>

      <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
        <Dropdown overlay={menu} trigger={["click"]}>
          <Button type="primary" icon={<PlusOutlined />}>
            Создать <DownOutlined />
          </Button>
        </Dropdown>

        {selectedRowKeys.length > 0 && (
          <Popconfirm
            title="Удалить выбранные элементы?"
            onConfirm={handleDeleteSelected}
          >
            <Button danger icon={<DeleteOutlined />}>
              Удалить выбранные
            </Button>
          </Popconfirm>
        )}
      </div>

      <Tabs defaultActiveKey="1">
        {/* Вкладка: Договоры */}
        <Tabs.TabPane tab="Договоры" key="1">
          <Table
            rowSelection={{
              selectedRowKeys,
              onChange: (keys) => {
                setSelectedRowKeys(keys);
                setSelectedDeleteType("contracts");
              },
            }}
            columns={[
              { title: "Номер", dataIndex: "number", key: "number" },
              { title: "Название", dataIndex: "name", key: "name" },
              { title: "Клиент", dataIndex: "client_name", key: "client_name" },
              {
                title: "Дата",
                dataIndex: "date",
                key: "date",
                render: (date) => dayjs(date).format("DD.MM.YYYY"),
              },
              { title: "Статус", dataIndex: "status", key: "status" },
            ]}
            dataSource={contracts}
            rowKey="id"
          />
        </Tabs.TabPane>

        {/* Вкладка: Спецификации */}
<Tabs.TabPane tab="Спецификации" key="2">
  <Table
    rowSelection={{
      selectedRowKeys,
      onChange: (keys) => {
        setSelectedRowKeys(keys);
        setSelectedDeleteType("specifications");
      },
    }}
    columns={[
      { title: "Номер", dataIndex: "number", key: "number" },
      {
        title: "Дата",
        dataIndex: "date",
        key: "date",
        render: (date) => dayjs(date).format("DD.MM.YYYY"),
      },
      { title: "Клиент", dataIndex: "client_name", key: "client_name" },
      {
        title: "Договор",
        dataIndex: "contract_number",
        key: "contract",
        render: (text) => text || "—"
      },
      {
        title: "Сумма",
        dataIndex: "total_amount", // Исправлено на total_amount
        key: "total_amount",
        render: (value) => {
          if (!value || value === "0.00") return "—";
          return `${Number(value).toLocaleString("ru-RU")} ₽`;
        }
      }
    ]}
    dataSource={specifications?.results || specifications || []} // Защита от undefined
    rowKey="id"
  />
</Tabs.TabPane>

{/* Вкладка: Счета на оплату */}
<Tabs.TabPane tab="Счета на оплату" key="3">
  <Table
    rowSelection={{
      selectedRowKeys,
      onChange: (keys) => {
        setSelectedRowKeys(keys);
        setSelectedDeleteType("invoices");
      }
    }}
    columns={[
      { title: "Номер", dataIndex: "number", key: "number" },
      {
        title: "Дата",
        dataIndex: "date",
        key: "date",
        render: (date) => dayjs(date).format("DD.MM.YYYY")
      },
      {
        title: "Клиент",
        key: "client",
        render: (_, record) => record.client?.name || "—"
      },
      {
        title: "Сумма",
        dataIndex: "total_amount",
        key: "amount",
        render: (value) =>
          value ? `${Number(value).toLocaleString("ru-RU")} ₽` : "—"
      },
      {
        title: "Договор",
        key: "contract",
        render: (_, record) => record.contract?.number || "—"
      },
      {
        title: "Спецификация",
        key: "specification",
        render: (_, record) => record.specification?.number || "—"
      },
      {
        title: "Статус",
        dataIndex: "status",
        key: "status",
        render: (status) => status || "—"
      }
    ]}
    dataSource={invoices?.results || invoices || []}
    rowKey="id"
  />
</Tabs.TabPane>

        {/* Вкладка: УПД */}
        <Tabs.TabPane tab="УПД" key="4">
          <Table
            rowSelection={{
              selectedRowKeys,
              onChange: (keys) => {
                setSelectedRowKeys(keys);
                setSelectedDeleteType("upds");
              },
            }}
            columns={[
              { title: "Номер", dataIndex: "number", key: "number" },
              {
                title: "Дата составления",
                dataIndex: "creation_date",
                key: "creation_date",
                render: (date) => dayjs(date).format("DD.MM.YYYY"),
              },
              { title: "Сумма", dataIndex: "amount", key: "amount" },
              { title: "Статус", dataIndex: "status", key: "status" },
            ]}
            dataSource={upds}
            rowKey="id"
          />
        </Tabs.TabPane>
      </Tabs>

      {/* Универсальное модальное окно */}
      <Modal
        title={`Создание ${getDocumentTypeLabel(modalType)}`}
        open={!!modalType}
        onCancel={() => setModalType(null)}
        onOk={handleCreate}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="number"
            label="Номер"
            rules={[{ required: true, message: "Обязательное поле" }]}
          >
            <Input />
          </Form.Item>

          {modalType !== "upd" && (
            <Form.Item name="name" label="Название">
              <Input />
            </Form.Item>
          )}

          <Form.Item
            name="client"
            label="Клиент"
            rules={[{ required: true, message: "Выберите клиента" }]}
          >
            <Select placeholder="Выберите клиента">
              {clients.map((client) => (
                <Option key={client.id} value={client.id}>
                  {client.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          {modalType === "invoice" && (
            <Form.Item
              name="amount"
              label="Сумма"
              rules={[{ required: true, message: "Введите сумму" }]}
            >
              <Input type="number" />
            </Form.Item>
          )}

          <Form.Item
            name="date"
            label="Дата"
            rules={[{ required: true, message: "Выберите дату" }]}
          >
            <DatePicker format="DD.MM.YYYY" />
          </Form.Item>

          {(modalType === "contract" || modalType === "specification") && (
            <Form.Item name="status" label="Статус">
              <Select placeholder="Выберите статус">
                <Option value="Подписан">Подписан</Option>
                <Option value="Не подписан">Не подписан</Option>
              </Select>
            </Form.Item>
          )}

          <Form.Item label="Файл">
            <Upload
              beforeUpload={() => false}
              onChange={({ fileList }) => setFileList(fileList)}
              fileList={fileList}
            >
              <Button icon={<UploadOutlined />}>Загрузить файл</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DocumentsPage;