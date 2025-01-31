import axios from "axios";

const API_URL = "http://localhost:8000/api/";

const api = axios.create({
  baseURL: API_URL,
});

// ✅ Функция для получения списка договоров
export const getContracts = async () => {
  try {
    const response = await api.get("documents/contracts/");
    return response.data;
  } catch (error) {
    console.error("Ошибка при загрузке договоров:", error);
    throw error;
  }
};

// ✅ Функция для создания нового договора
export const createContract = async (data) => {
  try {
    const response = await api.post("documents/contracts/", data, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при создании договора:", error.response?.data || error);
    throw error;
  }
};

// ✅ Функция для получения списка спецификаций
export const getSpecifications = async () => {
  try {
    const response = await api.get("documents/specifications/");
    return response.data;
  } catch (error) {
    console.error("Ошибка при загрузке спецификаций:", error);
    throw error;
  }
};

// ✅ Функция для создания спецификации
export const createSpecification = async (data) => {
  try {
    const response = await api.post("documents/specifications/", data, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при создании спецификации:", error.response?.data || error);
    throw error;
  }
};

// ✅ Функция для получения списка счетов
export const getInvoices = async () => {
  try {
    const response = await api.get("documents/invoices/");
    return response.data;
  } catch (error) {
    console.error("Ошибка при загрузке счетов:", error);
    throw error;
  }
};

// ✅ Функция для создания счета
export const createInvoice = async (data) => {
  try {
    const response = await api.post("documents/invoices/", data, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при создании счета:", error.response?.data || error);
    throw error;
  }
};

// ✅ Функция для получения списка УПД
export const getUPDs = async () => {
  try {
    const response = await api.get("documents/upds/");
    return response.data;
  } catch (error) {
    console.error("Ошибка при загрузке УПД:", error);
    throw error;
  }
};

// ✅ Функция для создания УПД (новая!)
export const createUPD = async (data) => {
  try {
    const response = await api.post("documents/upds/", data, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при создании УПД:", error.response?.data || error);
    throw error;
  }
};

// ✅ Функция для удаления договора
export const deleteContract = async (id) => {
  try {
    await api.delete(`documents/contracts/${id}/`);
    return true;
  } catch (error) {
    console.error("Ошибка при удалении договора:", error);
    throw error;
  }
};

// ✅ Функция для удаления спецификации
export const deleteSpecification = async (id) => {
  try {
    await api.delete(`documents/specifications/${id}/`);
    return true;
  } catch (error) {
    console.error("Ошибка при удалении спецификации:", error);
    throw error;
  }
};

// ✅ Функция для удаления счета
export const deleteInvoice = async (id) => {
  try {
    await api.delete(`documents/invoices/${id}/`);
    return true;
  } catch (error) {
    console.error("Ошибка при удалении счета:", error);
    throw error;
  }
};

// ✅ Функция для удаления УПД
export const deleteUPD = async (id) => {
  try {
    await api.delete(`documents/upds/${id}/`);
    return true;
  } catch (error) {
    console.error("Ошибка при удалении УПД:", error);
    throw error;
  }
};

// ✅ Функция для получения конкретного договора
export const getContractById = async (id) => {
  try {
    const response = await api.get(`documents/contracts/${id}/`);
    return response.data;
  } catch (error) {
    console.error(`Ошибка загрузки договора ID=${id}:`, error);
    throw error;
  }
};