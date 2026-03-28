FROM python:3.11-slim

# Install system libraries dlib and opencv need
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    libx11-6 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8080

CMD python manage.py migrate && gunicorn backend.wsgi --bind 0.0.0.0:$PORT
