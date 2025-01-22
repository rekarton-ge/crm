import requests
import logging

logger = logging.getLogger(__name__)


def check_contractor(inn):
    """
    Проверка контрагента по ИНН через API ФНС.
    Возвращает данные о контрагенте или None в случае ошибки.
    """
    api_key = "dba0487dabf8143272bd8ea509b673e5498bb10c"  # Замени на свой API-ключ
    url = f"https://api-fns.ru/api/egr?req={inn}&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем, что статус ответа 200
        data = response.json()

        # Проверяем, что ответ содержит данные
        if data and "Items" in data:
            return data["Items"][0]  # Возвращаем первый результат
        else:
            logger.warning(f"Нет данных для ИНН {inn}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API ФНС: {e}")
        return None