# Развёртывание на Render

Проект развёрнут на Render по адресу https://spoibd-pz5.onrender.com. Используются два бесплатных сервиса: **Postgres** (база данных) и **Web Service** (Django + Gunicorn). Платные услуги не нужны.

Процесс разделён на четыре этапа: сборка, миграции, запуск сервера, проверка.

## 0. Подготовка репозитория

В репозитории уже есть всё, что нужно Render:

| Файл | Зачем |
|---|---|
| `requirements.txt` | список пакетов, которые Render установит при сборке |
| `build.sh` | сценарий сборки: установка пакетов и `collectstatic`. Строки файла должны заканчиваться символом LF (в VS Code справа внизу `LF`, а не `CRLF`) |
| `config/settings.py` | читает секреты из переменных окружения, подключает WhiteNoise и PostgreSQL через `DATABASE_URL` |
| `.gitignore` | не пускает в репозиторий `.env`, `db.sqlite3`, `venv/`, `staticfiles/` |

## 1. База данных PostgreSQL

1. https://dashboard.render.com → **New → Postgres**.
2. Name — любое (например, `pz8-django-db`), Region — тот же, что будет у веб-сервиса, Plan — **Free** → **Create Database**.
3. Дождитесь статуса **Available**.
4. В разделе **Connections** находятся две строки подключения. Их значения содержат пароль: не публикуйте их в отчётах, скриншотах и в репозитории.
   - **Internal Database URL** — для веб-сервиса Render в том же регионе. Работает только внутри Render.
   - **External Database URL** — для подключения с вашего компьютера (миграции, создание пользователей).

Бесплатная база Render действует ограниченный срок (около 30 дней), затем её нужно создать заново и повторить шаги 3–4 этого руководства.

## 2. Web Service

1. **New → Web Service** → подключите GitHub → репозиторий `reallyspring/SPOiBD_PZ5`.
2. Настройки:

| Поле | Значение |
|---|---|
| Language | Python 3 |
| Branch | `main` |
| Region | как у базы данных |
| Root Directory | пусто |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --access-logfile -` |
| Instance Type | Free |

`config` — пакет настроек проекта, `$PORT` — порт, который назначает Render. Флаг `--access-logfile -` выводит каждый запрос в журнал Logs.

3. **Environment Variables:**

| Переменная | Значение | Назначение |
|---|---|---|
| `DATABASE_URL` | Internal Database URL из раздела Connections базы | подключение Django к PostgreSQL. Используется внутренний адрес: он работает внутри сети Render без выхода в интернет |
| `DJANGO_SECRET_KEY` | кнопка **Generate** | подпись сессий и CSRF-токенов. Не совпадает с локальным ключом |
| `DJANGO_DEBUG` | `False` | режим эксплуатации: при ошибке посетитель не видит код и настройки |
| `DJANGO_ALLOWED_HOSTS` | `spoibd-pz5.onrender.com` | домен без `https://`; запросы с другим заголовком Host получают 400 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://spoibd-pz5.onrender.com` | полный адрес с протоколом; без него POST/PATCH/DELETE получают 403 CSRF |

Если Render выдал другой адрес сервиса, подставьте его в две последние переменные.

4. **Deploy Web Service.**

## 3. Сборка и запуск

После каждого `git push` в ветку `main` Render автоматически:

1. скачивает код из GitHub;
2. выполняет `build.sh`: `pip install -r requirements.txt` и `python manage.py collectstatic --noinput` (статические файлы собираются в `staticfiles/`);
3. запускает Gunicorn командой Start Command.

Успешный запуск в журнале **Logs**: строки `Starting gunicorn`, `Booting worker` и `Your service is live`.

## 4. Миграции и начальные данные

Сборка не создаёт таблицы в базе. Миграции выполняются отдельно, вручную, один раз после изменения моделей. На бесплатном тарифе нет вкладки Shell, поэтому команды выполняются с компьютера через **External Database URL**.

Откройте **новое** окно PowerShell в папке проекта:

```powershell
venv\Scripts\activate
$env:DATABASE_URL="<External Database URL>"
python manage.py migrate
python manage.py showmigrations accounts
python manage.py seed_library
```

При первом развёртывании дополнительно:

```powershell
python manage.py seed_demo
python manage.py createsuperuser
```

Затем **закройте это окно**, чтобы следующие локальные запуски не работали с облачной базой. Переменная, заданная через `$env:`, сильнее значения из `.env` и действует только в этом окне.

После добавления новых моделей (например, миграции `0005_book_bookloan_loanevent` из СРС №7) нужно снова выполнить `migrate` и `seed_library` для облачной базы. Иначе страница с новыми моделями отвечает 500, а в Logs видно `relation "accounts_book" does not exist`.

Учётная запись методиста создаётся на сайте: `https://spoibd-pz5.onrender.com/admin/` → Users → Add user → в поле Groups выбрать «Методист» (группу создаёт `seed_library`).

## 5. Проверка

1. `https://spoibd-pz5.onrender.com/healthz/` → `{"status": "ok"}`: Django запущен через Gunicorn.
2. Вход и страница `/library/` открываются с оформлением Tabler: статика собрана и отдаётся WhiteNoise. В DevTools → Network CSS и JS отвечают 200.
3. Создание заявки: `POST /api/loans/` → 201.
4. Render → **Manual Deploy → Restart service**, затем обновить страницу: заявка на месте, данные хранятся в PostgreSQL.
5. Несуществующий адрес, например `/abc/`, показывает короткую страницу «Not Found» без трассировки: `DEBUG=False` действует.

## SQLite и PostgreSQL — разные базы

Локально проект работает с файлом `db.sqlite3`, на Render — с PostgreSQL. Данные между ними автоматически не переносятся: пользователи, заявки и учебники в облачной базе создаются отдельно (командами из раздела 4 и через сайт). Хранить данные в SQLite на Render нельзя: диск веб-сервиса очищается при каждом развёртывании и перезапуске.

## Обновление приложения

1. Изменить код, проверить локально, `git push`.
2. Дождаться в Logs `Your service is live`.
3. Если менялись модели — выполнить раздел 4 (`migrate`).
4. Проверить по разделу 5.
