## Flask API для загрузки документов

### Запуск

```bash
pip install -r api/requirements.txt
python api/app.py
```

По умолчанию сервер стартует на `0.0.0.0:8000`.

### Docker

Сборка (из корня репозитория):

```bash
docker build -t rag-api -f api/Dockerfile .
```

Запуск:

```bash
docker run --rm -p 8000:8000 rag-api
```

Если хочешь сохранять `docs/`, `db/`, `uploads/` на хосте (рекомендуется):

```bash
docker run --rm -p 8000:8000 ^
  -v "%cd%\docs:/app/docs" ^
  -v "%cd%\db:/app/db" ^
  -v "%cd%\uploads:/app/uploads" ^
  rag-api
```

### Проверка

- `GET /health`

### Загрузка файлов

- `POST /upload` (multipart/form-data)
  - поле `file` (один файл) **или** `files` (несколько файлов)
  - поддерживаемые расширения: `.pdf`, `.txt`
  - файлы сохраняются в папку `docs/` в корне репозитория (создаётся автоматически)

Пример (PowerShell):

```powershell
curl.exe -F "file=@.\some.pdf" http://localhost:8000/upload
```

### Настройки через переменные окружения

- `RAG_DOCS_DIR`: куда сохранять загрузки (по умолчанию `<repo>/docs`)
- `RAG_MAX_UPLOAD_MB`: лимит размера запроса в МБ (по умолчанию `50`)
- `PORT`: порт (по умолчанию `8000`)

