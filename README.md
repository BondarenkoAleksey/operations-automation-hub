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

Integration-тесты требуют запущенного PostgreSQL и применённой схемы БД:

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run pytest -m integration
```

Проверить текущую revision Alembic:

```bash
uv run alembic current
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

#### Восстановление локальной БД после `docker compose down -v`

> `docker compose down -v` удаляет named volume `postgres_data`.
> Для этого учебного проекта это допустимо только для локальной БД с синтетическими данными.
> После удаления volume PostgreSQL запускается с чистой БД без таблиц и Alembic revision.

Чтобы восстановить локальную схему БД:

```bash
docker compose up -d postgres
docker compose ps
uv run alembic upgrade head
uv run alembic current
uv run pytest -m integration
```

Ожидаемый результат `uv run alembic current` — текущая последняя Alembic revision с отметкой `(head)`.

Подключиться к БД + SQL-команда для проверки

```bash
docker compose exec postgres psql -U operations_user -d operations_automation_hub -c "SELECT current_database(), current_user;"
```

#### PostgreSQL работает в Docker, но Python получает `Connection refused`

Если контейнер имеет статус `healthy`, но Python/FastAPI, запущенный на macOS, не подключается к `localhost:5432`, проверь публикацию порта:

```bash
docker compose ps
docker compose port postgres 5432
```

В выводе `docker compose ps` должен быть опубликованный порт, похожий на:

```text
0.0.0.0:5432->5432/tcp
```

Если отображается только:

```text
5432/tcp
```

PostgreSQL доступен лишь внутри Docker network, а приложение, запущенное на хост-машине, не сможет подключиться к `localhost:5432`.

Для пересоздания контейнера без удаления named volume:

```bash
docker compose up -d --force-recreate postgres
```

### PostgreSQL: важные моменты

- Локальные переменные PostgreSQL лежат в `.env`.
- `.env` создаётся на основе `.env.example`.
- `.env` не коммитится.
- При запуске FastAPI на хосте используйте `POSTGRES_HOST=localhost`.
- Когда FastAPI будет запущен в Docker Compose, hostname будет `postgres` — имя Compose-сервиса.
- Внутри Docker-контейнера `localhost` указывает на сам контейнер FastAPI, а не на PostgreSQL.


### CSV-валидация

`POST /imports/csv/validate` — проверка CSV-файла с заявками **без сохранения в базу**.
Endpoint принимает multipart-файл и возвращает результат проверки: какие заявки
корректны, какие поля содержат ошибки и какие `external_request_id` повторяются.
Это не импорт в PostgreSQL и не создание Job — только валидация.

Ожидаемый результат: HTTP 200; две валидные заявки в исходном порядке;
одна ошибка суммы у записи №4; один повторяющийся ID (`DEMO-001`).

#### Пример

Синтетический пример: [examples/csv/validation_demo.csv](examples/csv/validation_demo.csv).

```bash
curl -sS \
  -F "file=@examples/csv/validation_demo.csv;type=text/csv" \
  -w '\nHTTP %{http_code}\n' \
  http://127.0.0.1:8000/imports/csv/validate
```

### Поля результата

| Поле | Значение |
|---|---|
| `valid_records` | Заявки, прошедшие проверку полей, в исходном порядке (включая повторяющиеся) |
| `issues` | Ошибки полей заявок: номер записи (`record_number`, заголовок — №1), имя поля, сообщение, код типа ошибки |
| `duplicate_request_ids` | Повторяющиеся `external_request_id` среди валидных заявок, отсортированные, без повторов |

### HTTP-статусы

| Статус | Значение |
|---|---|
| 200 | Файл проверен; ошибки отдельных заявок и дубли находятся в результате |
| 400 | Ошибка структуры, CSV-парсера или кодировки UTF-8 |
| 413 | Содержимое файла превышает 1 MiB |
| 422 | Отсутствует обязательный файл либо нарушен контракт входного запроса |


### Ограничения

- Принимается только CSV в кодировке UTF-8.
- Endpoint ничего не сохраняет в БД и не создаёт Job.
- Повторяющиеся заявки остаются в `valid_records`.
  В `duplicate_request_ids` перечислены только их идентификаторы.
- Размер проверяется после приёма multipart-загрузки и не защищает сервер
  от большого HTTP-запроса на уровне веб-сервера.

### Полезная информация

Запуск uvicorn на 8000 порте с автоперезагрузкой.

```bash
uv run uvicorn operations_automation_hub.main:app --reload --host 127.0.0.1 --port 8000
```

Для обычной остановки сервера нажми `Ctrl+C` в терминале, где он запущен.

Поиск процессов, слушающих 8000 порт.

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Завершить процесс.
```text
kill PID
```

Аварийное завершение всех процессов, в командной строке которых встречается `uvicorn`.

Использовать только если обычная остановка не помогла.
Команда может затронуть серверы других проектов и не позволяет выполнить
штатную очистку ресурсов.

```bash
pkill -9 -f uvicorn
```

## Текущий статус

Этап 0: настройка Python-проекта, uv, pytest и Ruff.

Этап 1: минимальный FastAPI: эндпоинты GET и POST, первые тесты, Pydantic схемы, запуск Uvicorn

Этап 2: PostgreSQL и SQLAlchemy
