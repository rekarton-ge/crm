# Используем официальный образ Python
FROM python:3.11.11-slim-bullseye

# Устанавливаем зависимости для PostgreSQL и других библиотек
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app/backend

# Копируем requirements и устанавливаем зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта
COPY backend/ .

# Открываем порт для Django
EXPOSE 8000

# Команда для запуска сервера разработки Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]