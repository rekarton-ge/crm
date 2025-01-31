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

      formData.append("number", values.number);
      formData.append("name", values.name || "");
      formData.append("client", values.client);
      formData.append("date", values.date.format("YYYY-MM-DD"));
      formData.append("status", values.status || "");

      if (fileList.length > 0) {
        formData.append("file", fileList[0].originFileObj);
      }

      if (modalType === "contract") {
        await createContract(formData);
        message.success("Договор успешно создан");
      }

      fetchAllData();
      setModalType(null);
      form.resetFields();
      setFileList([]);
    } catch (error) {
      message.error("Ошибка при создании договора");
    }
  };

  const handleDeleteSelected = async () => {
    try {
      if (selectedDeleteType === "contracts") {
        await Promise.all(selectedRowKeys.map(id => deleteContract(id)));
        message.success("Выбранные договоры удалены");
      }

      setSelectedRowKeys([]);
      fetchAllData();
    } catch (error) {
      message.error("Ошибка при удалении");
    }
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
          <Popconfirm title="Удалить выбранные элементы?" onConfirm={handleDeleteSelected}>
            <Button type="danger" icon={<DeleteOutlined />}>
              Удалить выбранные
            </Button>
          </Popconfirm>
        )}
      </div>

      <Tabs defaultActiveKey="1">
        <Tabs.TabPane tab="Договоры" key="1">
          <Table
            rowSelection={{
              selectedRowKeys,
              onChange: (keys) => {
                setSelectedRowKeys(keys);
                setSelectedDeleteType("contracts");
              }
            }}
            columns={[
              { title: "Номер", dataIndex: "number", key: "number" },
              { title: "Название", dataIndex: "name", key: "name" },
              { title: "Клиент", dataIndex: "client_name", key: "client_name" },
              { title: "Дата", dataIndex: "date", key: "date", render: date => dayjs(date).format("DD.MM.YYYY") },
              { title: "Статус", dataIndex: "status", key: "status" }
            ]}
            dataSource={contracts}
            rowKey="id"
          />
        </Tabs.TabPane>
      </Tabs>

      {/* ✅ МОДАЛЬНОЕ ОКНО СОЗДАНИЯ ДОГОВОРА */}
      <Modal
        title="Создание договора"
        open={modalType === "contract"}
        onCancel={() => setModalType(null)}
        onOk={handleCreate}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="number" label="Номер договора" rules={[{ required: true, message: "Введите номер" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="Название договора">
            <Input />
          </Form.Item>
          <Form.Item name="client" label="Клиент" rules={[{ required: true, message: "Выберите клиента" }]}>
            <Select placeholder="Выберите клиента">
              {clients.map(client => (
                <Option key={client.id} value={client.id}>{client.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="date" label="Дата" rules={[{ required: true, message: "Выберите дату" }]}>
            <DatePicker format="DD.MM.YYYY" />
          </Form.Item>
          <Form.Item name="status" label="Статус">
            <Select>
              <Option value="Подписан">Подписан</Option>
              <Option value="Не подписан">Не подписан</Option>
              <Option value="На согласовании">На согласовании</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Файл">
            <Upload beforeUpload={() => false} onChange={({ fileList }) => setFileList(fileList)} fileList={fileList}>
              <Button icon={<UploadOutlined />}>Загрузить</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DocumentsPage;