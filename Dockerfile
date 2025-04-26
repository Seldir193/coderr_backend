FROM python:3.12.10-slim-bookworm

########################  Arbeits­verzeichnis  ######################
WORKDIR /app                     # ← hier liegt manage.py




######## 1. Requirements separat kopieren (Cache-Layer) #############
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

##################### 2. Projektcode kopieren #######################
COPY . .

################# 3. Statische Dateien einsammeln ###################
RUN python manage.py collectstatic --noinput

################ 4. Unprivilegierter Nutzer (optional) ##############
RUN useradd -m appuser
USER appuser

############## 5. Port & Runtime-Umgebung setzen ####################
EXPOSE 8000
ENV PYTHONUNBUFFERED=1

################## 6. Start-Kommando anpassen #######################
CMD ["gunicorn", "Coder.wsgi:application", "--bind", "0.0.0.0:8000"]
#                 └───── Projektordner.wsgi:application  (Groß-/Klein beachten)
