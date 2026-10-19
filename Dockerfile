# Образ: Python 3.11 — версия из задания
FROM python:3.11-slim

WORKDIR /app

# Сначала только зависимости — Docker закэширует этот слой,
# и пересборка после правок кода будет занимать секунды
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Теперь сам код
COPY . .

# Вечная программа в контейнере: без Ctrl+C-обёрток, пусть Docker
# сам следит, что процесс жив (restart: unless-stopped в compose)
CMD ["python", "-u", "main.py"]
