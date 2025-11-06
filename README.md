# Веб-скрапер "Books to Scrape"

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Linter](https://img.shields.io/badge/linter-pylint-yellowgreen.svg)](https://www.pylint.org/)
[![Typing](https://img.shields.io/badge/typing-mypy-blue.svg)](http://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org)

Это учебный проект, демонстрирующий навыки веб-скрапинга, автоматизации и тестирования на Python. Скрипт рекурсивно парсит весь каталог сайта [books.toscrape.com](http://books.toscrape.com), собирает подробную информацию о каждой книге и сохраняет результат в `json` (форматированный как `.txt`).

Проект также настроен на автоматический ежедневный запуск с использованием `schedule`.

## Основные возможности

* **Рекурсивный парсинг:** Сбор данных со всех 50 страниц каталога.
* **Многопоточность:** Использование `ThreadPoolExecutor` для одновременной загрузки данных о книгах, что значительно ускоряет процесс.
* **Сбор полных данных:** Парсинг названия, цены, рейтинга, наличия, UPC, описания и всех полей из таблицы "Product Information".
* **Автоматизация:** Настроен запуск по расписанию (ежедневно) с помощью библиотеки `schedule`.
* **Сохранение данных:** Результаты сохраняются в файл `artifacts/books_data.txt`.
* **Качество кода:** Код проверен с помощью `pylint` и `mypy`, а также покрыт тестами `pytest`.

## Структура проекта

```
books_scraper/
├── artifacts/          # Результаты парсинга
│   └── books_data.txt
├── notebooks/          # Jupyter ноутбуки
│   └── HW_03_python_ds_2025.ipynb
├── tests/              # Тесты
│   └── test_scraper.py
├── scraper.py          # Основной скрипт парсера
├── requirements.txt    # Зависимости проекта
├── .gitignore          # Исключения для Git
├── .pylintrc           # Конфигурация pylint
├── mypy.ini            # Конфигурация mypy
└── README.md           # Документация проекта
```

## Установка и запуск

Для запуска проекта на локальной машине выполните следующие шаги:

1.  **Клонируйте репозиторий:**
    ```bash
    git clone [https://github.com/SergeiVolkhin/HW_03.git](https://github.com/SergeiVolkhin/HW_03.git)
    cd HW_03
    ```

2.  **Создайте и активируйте виртуальное окружение:**
    * На macOS/Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    * На Windows:
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```

3.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Запустите парсер в режиме планировщика:**
    Скрипт запустится и будет ожидать заданного времени (по умолчанию 12:00 + тестовый запуск через 60 секунд) для выполнения парсинга.
    ```bash
    python scraper.py
    ```
    *Результат (1000 книг) будет сохранен в `artifacts/books_data.txt`.*

## Запуск тестов

Для проверки корректности работы ключевых функций (парсинг одной книги, парсинг нескольких страниц, обработка ошибок) можно запустить автотесты:

```bash
pytest -v
```