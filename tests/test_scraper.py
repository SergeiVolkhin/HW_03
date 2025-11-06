#!/usr/-bin/env python3
"""
Автотесты для модуля парсинга книг (scraper.py)
"""
# pylint: disable=redefined-outer-name

import sys
import os
from typing import Iterator
import pytest
import requests

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)


try:
    from scraper import get_book_data, scrape_books, BookData  # <--- BookData ТЕПЕРЬ ИСПОЛЬЗУЕТСЯ
except ImportError:
    print("Ошибка: Не удалось импортировать 'scraper.py'.")
    print(f"Ожидаемый путь к файлу: {parent_dir}/scraper.py")
    sys.exit(1)


@pytest.fixture(scope="module")
def session() -> Iterator[requests.Session]:
    """
    Pytest-фикстура, которая создает одну requests.Session для всех тестов
    в этом модуле. Это экономит ресурсы (переиспользование соединения).
    """
    print("\n[Fixture] Создание сессии requests...")
    with requests.Session() as s:
        s.headers.update({
            'User-Agent': 'Pytest Scraper Test'
        })
        yield s
    print("\n[Fixture] Закрытие сессии requests.")


def test_get_book_data_parsing(session: requests.Session) -> None:
    """
    Тест 1: Проверяем, что get_book_data корректно парсит
    конкретную, известную страницу книги.
    """
    book_url = ('http://books.toscrape.com/catalogue/'
                'a-light-in-the-attic_1000/index.html')

    data: BookData = get_book_data(session, book_url)

    # Проверка, что данные не пустые
    assert data is not None
    assert isinstance(data, dict)
    assert data != {}

    # Проверка ключевых полей
    assert data['title'] == 'A Light in the Attic'
    assert data['rating'] == 3
    assert data['price'] == '£51.77'
    assert data['UPC'] == 'a897fe39b1053632'
    assert data['url'] == book_url

    stock_value = data.get('stock')
    assert isinstance(stock_value, str)
    assert 'In stock (22 available)' in stock_value


def test_scrape_books_page_limit() -> None:
    """
    Тест 2: Проверяем, что scrape_books с max_pages=1
    собирает ровно 20 книг (количество на одной странице).
    """
    print("\n[Test] Запуск scrape_books(max_pages=1)...")
    books = scrape_books(max_pages=1)

    # Проверка типа и количества
    assert isinstance(books, list)
    assert len(books) == 20

    # Создаем множество (set) всех названий из 20 собранных книг
    titles = {book['title'] for book in books if 'title' in book}

    # Проверяем, что наши книги есть в этом множестве
    assert 'A Light in the Attic' in titles
    assert 'Tipping the Velvet' in titles


def test_get_book_data_network_error(session: requests.Session) -> None:
    """
    Тест 3: Проверяем, что get_book_data корректно обрабатывает
    ошибку (например, 404) и возвращает пустой словарь.
    """
    invalid_url = 'http://books.toscrape.com/catalogue/non-existent-book-9999.html'

    data: BookData = get_book_data(session, invalid_url)

    # Ожидаем пустой словарь в случае ошибки
    assert data == {}
