# Типичные ошибки и диагностика

Общий порядок диагностики:

1. Прочитать последнюю строку ошибки в терминале (локально) или во вкладке **Logs** (Render).
2. Проверить, активировано ли виртуальное окружение (`(venv)` в начале строки) и находится ли терминал в папке с `manage.py`.
3. Проверить переменные окружения: локально — файл `.env`, на Render — раздел Environment.
4. Для ошибок на страницах открыть DevTools (F12) → Network и посмотреть код ответа и тело ответа API.

## 1. Не активируется виртуальное окружение

**Симптом.** `venv\Scripts\activate` выводит: `File ...\Activate.ps1 cannot be loaded because running scripts is disabled on this system`.

**Причина.** Политика PowerShell запрещает запуск скриптов.

**Исправление.** Разрешить скрипты для текущего окна и повторить активацию:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
```

## 2. pip не находит Django==6.1.1

**Симптом.** `pip install -r requirements.txt` завершается ошибкой `ERROR: Could not find a version that satisfies the requirement Django==6.1.1` и `No matching distribution found`.

**Причина.** Django 6.1 устанавливается только на Python 3.12 и новее, а окружение создано старой версией Python.

**Диагностика.** `python --version` внутри активированного окружения.

**Исправление.** Установить Python 3.12+ с python.org, удалить папку `venv` и создать окружение заново: `py -3.13 -m venv venv` (вместо 3.13 — установленная версия).

## 3. Django не запускается: Set DJANGO_SECRET_KEY

**Симптом.** Любая команда `python manage.py ...` завершается строкой `django.core.exceptions.ImproperlyConfigured: Set DJANGO_SECRET_KEY`.

**Причина.** Нет файла `.env` или в нём нет `DJANGO_SECRET_KEY`. Ключ намеренно не хранится в коде.

**Диагностика.** `Test-Path .env` → `False`, либо в `.env` нет строки с ключом.

**Исправление.** `Copy-Item .env.example .env`, при необходимости заменить значение ключа.

## 4. settings.DATABASES is improperly configured

**Симптом.** `ImproperlyConfigured: settings.DATABASES is improperly configured. Please supply the ENGINE value.`

**Причина.** В `.env` есть строка `DATABASE_URL=` с пустым значением. Пустая строка считается заданным адресом, поэтому SQLite по умолчанию не подключается.

**Исправление.** Удалить строку или закомментировать её символом `#`, как в `.env.example`.

## 5. no such table / relation does not exist

**Симптом.** Страница отвечает 500. Локально в терминале `OperationalError: no such table: accounts_book`, на Render в Logs `ProgrammingError: relation "accounts_book" does not exist`.

**Причина.** Миграции не применены к той базе, с которой работает приложение. Частый случай — после `git pull` с новыми моделями или после создания новой базы на Render.

**Диагностика.** `python manage.py showmigrations accounts`: у непримененных миграций стоит `[ ]`.

**Исправление.** Локально `python manage.py migrate`. Для Render — `migrate` с External Database URL (см. [deployment.md](deployment.md), раздел 4).

## 6. Страница без оформления или Missing staticfiles manifest entry

**Симптом.** При `DJANGO_DEBUG=False` страницы отвечают 500, в журнале `ValueError: Missing staticfiles manifest entry for 'vendor/tabler/css/tabler.min.css'`. Либо страница открывается без стилей, в Network CSS-файлы отвечают 404.

**Причина.** В режиме эксплуатации статику отдаёт WhiteNoise из папки `staticfiles/`, а она не собрана.

**Исправление.** `python manage.py collectstatic --noinput`. На Render эта команда входит в `build.sh`; в Logs сборки должна быть строка `... static files copied ...`. Для локальной разработки достаточно `DJANGO_DEBUG=True`.

## 7. collectstatic: references a file which could not be found (.map)

**Симптом.** `The CSS file 'vendor/tabler/css/tabler.min.css' references a file which could not be found: vendor/tabler/css/tabler.min.css.map`.

**Причина.** Хранилище `CompressedManifestStaticFilesStorage` проверяет ссылки внутри CSS и JS, а файлов карт кода `.map` в проекте нет.

**Исправление.** Удалить последнюю строку с `sourceMappingURL` в `tabler.min.css`, `tabler.min.js`, `chart.umd.min.js`, `static/js/chart.js`. В репозитории это уже сделано; ошибка появится снова, если заменить эти файлы свежими копиями из `node_modules`.

## 8. Bad Request (400) и DisallowedHost

**Симптом.** Любая страница отвечает `Bad Request (400)`. В журнале `Invalid HTTP_HOST header: 'spoibd-pz5.onrender.com'. You may need to add 'spoibd-pz5.onrender.com' to ALLOWED_HOSTS.`

**Причина.** Домена нет в `DJANGO_ALLOWED_HOSTS` либо он указан с `https://` или с опечаткой.

**Исправление.** `DJANGO_ALLOWED_HOSTS=spoibd-pz5.onrender.com` (только домен), сохранить переменную и дождаться перезапуска.

## 9. 403 CSRF verification failed при отправке форм

**Симптом.** Вход или кнопки на странице получают 403, в ответе `CSRF verification failed. Request aborted.` или `Origin checking failed`.

**Причина.** Адреса сайта нет в `DJANGO_CSRF_TRUSTED_ORIGINS` или он указан без `https://`.

**Исправление.** `DJANGO_CSRF_TRUSTED_ORIGINS=https://spoibd-pz5.onrender.com`. Локально — `http://127.0.0.1:8000`. Обновить страницу, чтобы получить новый CSRF-токен.

## 10. У методиста нет кнопок «Выдать», «Зачислить»

**Симптом.** Пользователь `methodist` видит страницу студента, на запросы изменения статуса получает «Недостаточно прав для этого действия.» (403).

**Причина.** Пользователь не состоит в группе «Методист», или группа названа иначе (лишний пробел, латинская буква).

**Исправление.** Выполнить `python manage.py seed_library` (создаёт группу с правильным названием), затем в `/admin/` добавить пользователя в эту группу.

## 11. Build failed на Render: $'\r': command not found

**Симптом.** Сборка на Render падает, в Logs `build.sh: line 2: $'\r': command not found`.

**Причина.** Файл `build.sh` сохранён в Windows с окончаниями строк CRLF.

**Исправление.** Открыть `build.sh` в VS Code, справа внизу нажать `CRLF` → выбрать `LF`, сохранить, сделать commit и push.

## 12. Первое открытие сайта на Render занимает около минуты

**Симптом.** После перерыва страница долго грузится, затем открывается нормально.

**Причина.** Бесплатный веб-сервис засыпает после 15 минут без запросов. Это не ошибка.
