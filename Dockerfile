# Usa una imagen oficial de Python como base
FROM python:3.9-slim-buster

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos a la imagen
COPY ./requirements.txt ./requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos al directorio de trabajo
COPY . .

# Ejecuta el script al iniciar el contenedor
CMD [ "python", "./binance-bot.py" ]
