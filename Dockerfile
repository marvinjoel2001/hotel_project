# Usa una imagen base oficial de Python
FROM python:3.10-slim-buster

# Establece variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Comentamos esta línea por ahora
# ENV DJANGO_SETTINGS_MODULE=your_project.settings

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instala las dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el proyecto
COPY . /app/

# Comentamos la recolección de archivos estáticos por ahora
# RUN python manage.py collectstatic --noinput

# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 8000

# Modificamos el comando para usar el servidor de desarrollo de Django por ahora
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]