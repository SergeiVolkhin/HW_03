#!/usr/bin/env python3
"""
Модуль для парсинга данных о книгах с сайта Books to Scrape

Этот модуль содержит функции для извлечения информации о книгах,
автоматизации процесса сбора данных и их сохранения
"""

import os
import time
import json
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Union, Optional
import requests
from typing_extensions import TypeAlias
from bs4 import BeautifulSoup, Tag
from requests.sessions import Session
import schedule

# Псевдонимы типов
BookData: TypeAlias = Dict[str, Union[str, int, None]]
BookList: TypeAlias = List[BookData]


# Константы
BASE_URL = 'https://books.toscrape.com'
CATALOGUE_URL_TEMPLATE = 'https://books.toscrape.com/catalogue/page-{}.html'
RATING_MAP = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
DEFAULT_TIMEOUT = 10
MAX_WORKERS = 10


# pylint: disable=too-many-locals
def get_book_data(session: Session, book_url: str) -> BookData:
    """
    Извлекает данные о книге с указанной страницы

    Args:
        session (Session): Сессия requests для выполнения запроса
        book_url (str): URL страницы книги

    Returns:
        BookData: Словарь с данными о книге.
                  Возвращает пустой словарь в случае ошибки сети.
    """
    try:
        response = session.get(book_url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение основных данных
        title_element = soup.find('h1')
        title = title_element.text.strip() if title_element else None

        price_element = soup.find('p', class_='price_color')
        price = price_element.text.strip() if price_element else None

        # Извлечение рейтинга
        rating = 0
        rating_element = soup.find('p', class_='star-rating')
        if isinstance(rating_element, Tag) and 'class' in rating_element.attrs:
            rating_classes = rating_element['class']
            if isinstance(rating_classes, list) and len(rating_classes) > 1:
                rating = RATING_MAP.get(rating_classes[1], 0)

        # Извлечение количества в наличии
        stock_element = soup.find('p', class_='instock availability')
        stock = stock_element.text.strip() if stock_element else None

        # Извлечение описания
        description = None
        description_header = soup.find('div', id='product_description')
        if description_header:
            description_element = description_header.find_next_sibling('p')
            description = description_element.text.strip() \
                if description_element else None

        # Извлечение характеристик из таблицы
        info = {}
        info_table = soup.find('table', class_='table table-striped')
        if isinstance(info_table, Tag):
            rows = info_table.find_all('tr')
            for row in rows:
                th_element = row.find('th')
                td_element = row.find('td')
                if th_element and td_element:
                    info_key = th_element.text.strip()
                    info_value = td_element.text.strip()
                    info[info_key] = info_value

        return {
            'title': title,
            'price': price,
            'rating': rating,
            'stock': stock,
            'description': description,
            'url': book_url,
            **info
        }

    except requests.RequestException as exc:
        print(f"Ошибка при загрузке {book_url}: {exc}")
        return {}


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def scrape_books(is_save: bool = False,
                max_pages: Optional[int] = None) -> BookList:
    """
    Парсит все страницы каталога и собирает данные о книгах с использованием
    многопоточности

    Args:
        is_save (bool): Если True, сохраняет данные в файл books_data.txt
                       в папке artifacts/
        max_pages (Optional[int]): Максимальное количество страниц для
                                  парсинга. Если None, парсит все страницы

    Returns:
        BookList: Список словарей с данными о книгах
    """
    print("Начало парсинга книг")

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'MyBookScraper (student project)'
        })

        # Проверка доступности сайта
        try:
            response = session.get(BASE_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            print(f"Сайт {BASE_URL} доступен")
        except requests.RequestException as exc:
            print(f"Сайт {BASE_URL} недоступен: {exc}")
            return []

        # Сбор всех URL книг
        all_book_urls = []
        page = 1

        while True:
            if max_pages and page > max_pages:
                break

            page_url = CATALOGUE_URL_TEMPLATE.format(page)

            try:
                response = session.get(page_url, timeout=DEFAULT_TIMEOUT)
                if response.status_code != 200:
                    print(f"Страница {page} недоступна. Завершение сбора URL.")
                    break

                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                book_links = soup.select('article.product_pod h3 a')

                if not book_links:
                    print(f"Страница {page} пуста. Завершение сбора URL.")
                    break

                for link in book_links:
                    href_value = link.get('href')

                    if isinstance(href_value, str):
                        book_url = urljoin(page_url, href_value)
                        all_book_urls.append(book_url)

                print(f"Найдено {len(book_links)} книг на странице {page}")
                page += 1

            except requests.RequestException as exc:
                print(f"Ошибка при загрузке страницы {page_url}: {exc}")
                break

        print(f"Всего найдено {len(all_book_urls)} книг для парсинга")

        if not all_book_urls:
            print("Не найдено ни одной книги для парсинга")
            return []

        parsed_books = []
        failed_count = 0
        total_books = len(all_book_urls)
        print(f"Запуск {MAX_WORKERS} потоков для обработки {total_books} книг...")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(get_book_data, session, url): url
                for url in all_book_urls
            }

            for i, future in enumerate(as_completed(futures), 1):
                url = futures[future]
                try:
                    book_data = future.result()
                    if book_data:
                        parsed_books.append(book_data)
                    else:
                        failed_count += 1
                        print(f"\n[Поток] Не удалось получить данные для: {url}")
                except Exception as exc:
                    failed_count += 1
                    print(f"\n[Поток] Ошибка при обработке {url}: {exc}")

                print(f"Обработано: {i}/{total_books} (Ошибок: {failed_count})",
                      end="\r")

    print()
    print("=" * 30)
    print("Парсинг завершен.")
    print(f"Успешно обработано {len(parsed_books)} книг, "
          f"неудачных попыток: {failed_count}")

    if is_save and parsed_books:
        save_books_data(parsed_books)

    return parsed_books


def save_books_data(book_list: BookList,
                   filename: str = 'books_data.txt') -> None:
    """
    Сохраняет данные о книгах в файл

    Args:
        book_list (BookList): Список данных о книгах
        filename (str): Имя файла для сохранения
    """
    try:
        artifacts_dir = 'artifacts'
        os.makedirs(artifacts_dir, exist_ok=True)
        filepath = os.path.join(artifacts_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(book_list, file, ensure_ascii=False, indent=4)

        print(f"Данные о {len(book_list)} книгах сохранены в {filepath}")

    except (OSError, IOError) as exc:
        print(f"Ошибка при сохранении данных: {exc}")


def run_scraper() -> None:
    """
    Функция для запуска парсера и сохранения данных в файл
    """
    print(f"Запуск парсинга в {time.strftime('%H:%M:%S')}")
    try:
        scraped_books = scrape_books(is_save=True)
        if scraped_books:
            print(f"Парсинг завершен успешно. Обработано {len(scraped_books)} книг.")
        else:
            print("Парсинг не выполнен: нет данных")
    except Exception as exc:
        print(f"Ошибка при выполнении парсинга: {exc}")


def main_loop(target_time: str = "12:00", test_delay: int = 60) -> None:
    """
    Основной цикл для проверки и выполнения задач по расписанию
    """
    schedule.every().day.at(target_time).do(run_scraper)
    print(f"Планировщик настроен на запуск каждый день в {target_time}")

    if test_delay:
        test_time_dt = time.localtime(time.time() + test_delay)
        test_time_str = time.strftime("%H:%M:%S", test_time_dt)
        schedule.every().day.at(test_time_str).do(run_scraper)
        print(f"Добавлен тестовый запуск в {test_time_str}")

    try:
        print("Запуск основного цикла планировщика")
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания. Остановка планировщика.")
    except Exception as exc:
        print(f"Ошибка в основном цикле: {exc}")


if __name__ == "__main__":
    main_loop()
