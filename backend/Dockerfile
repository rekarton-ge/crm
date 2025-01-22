# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт 8000 для доступа к Django
EXPOSE 8000

# Команда для запуска сервера разработки Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]