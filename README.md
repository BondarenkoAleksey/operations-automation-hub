# Operations Automation Hub

Учебный Python Backend-проект: внутренняя платформа для автоматизации первичной обработки операционных заявок.

## Цель проекта

Система будет принимать CSV/XLSX-файлы с синтетическими заявками, валидировать их, сохранять данные в PostgreSQL и запускать фоновую обработку через внешние mock-интеграции.

Проект не использует реальные персональные, банковские или чувствительные данные.

## Технологии

- Python 3.12
- uv
- pytest
- Ruff
- FastAPI

Стек будет расширяться постепенно: PostgreSQL, SQLAlchemy, Alembic, Docker, Redis, Celery, интеграции и мониторинг.

## Подготовка окружения

Установить зависимости и создать виртуальное окружение:

```bash
uv sync
```

Проверить версию Python, используемую проектом:

```bash
uv run python --version
```

## Проверки качества

Запустить тесты:

```bash
uv run pytest
```
По умолчанию `uv run pytest` запускает тесты без внешней инфраструктуры.

Integration-тесты требуют запущенного PostgreSQL:

```bash
docker compose up -d
uv run pytest -m integration
```

Проверить код линтером:

```bash
uv run ruff check .
```

Проверить форматирование:

```bash
uv run ruff format --check .
```

Применить автоматическое форматирование:

```bash
uv run ruff format .
```

## Дополнительно

### Как создать `.env`

Создайте локальный файл переменных окружения на основе шаблона:

```bash
cp .env.example .env
```
При необходимости измените значение `POSTGRES_PASSWORD` в локальном файле `.env`. Файл `.env` не должен попадать в Git.

### Как поднять PostgreSQL

Перед запуском установите и запустите Docker Desktop

Проверить итоговую конфигурацию Docker Compose:

```bash
docker compose config
```
Запустить PostgreSQL в фоновом режиме:

```bash
docker compose up -d
```
или для повторного запуска

```bash
docker compose start postgres
```

Проверить статус

```bash
docker compose ps
```

Проверка готовности через pg_isready

```bash
docker compose exec postgres pg_isready -U operations_user -d operations_automation_hub
```

Посмотреть логи

```bash
docker compose logs postgres
```

Остановить контейнер, без его удаления

```bash
docker compose stop
```

Удалить контейнер (останавливает и удаляет контейнеры и сеть проекта, но сохраняет named volume `postgres_data` и данные PostgreSQL)

```bash
docker compose down
```

Удалить контейнер (дополнительно удаляет named volume, поэтому локальная база будет полностью очищена)

```bash
docker compose down -v
```

Подключиться к БД + SQL-команда для проверки

```bash
docker compose exec postgres psql -U operations_user -d operations_automation_hub -c "SELECT current_database(), current_user;"
```

### PostgreSQL: важные моменты

- Локальные переменные PostgreSQL лежат в `.env`.
- `.env` создаётся на основе `.env.example`.
- `.env` не коммитится.
- При запуске FastAPI на хосте используйте `POSTGRES_HOST=localhost`.
- Когда FastAPI будет запущен в Docker Compose, hostname будет `postgres` — имя Compose-сервиса.
- Внутри Docker-контейнера `localhost` указывает на сам контейнер FastAPI, а не на PostgreSQL.

## Текущий статус

Этап 0: настройка Python-проекта, uv, pytest и Ruff.

Этап 1: минимальный FastAPI: эндпоинты GET и POST, первые тесты, Pydantic схемы, запуск Uvicorn

Этап 2: PostgreSQL и SQLAlchemy
