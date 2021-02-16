import os
import base64
from datetime import datetime


def strip_time(dt: datetime) -> str:
    """
    Отрезает время из даты-времени

    Пример:
    16.12.2020 00:00:00 -> 16.12.2020
    """
    return dt.strftime('%d.%m.%Y')


def load_file(directory: str, filename: str, extensions: tuple) -> bytes:
    """
    Загружает файл из выбранной директории и возвращает байты
    Параметры:
        directory: директория в папке media в которой находится файл
        filename: название файла без расширения (передавать "photo_name", не "photo_name.jpg")
        extensions: расширения, под которым может быть файл
    Возвращает:
        Байты - содержимое файла.
        Если файл не найден, вернёт пустоту b''
    """
    assert type(directory) == str, f'Получил тип {type(directory)}'
    assert type(filename) == str, f'Получил тип {type(filename)}'
    assert type(extensions) == tuple, f'Получил тип {type(extensions)}'
    path = os.path.join("media", directory, filename)
    for ext in extensions:
        if os.path.exists(path+ext):
            with open(path+ext, "rb") as f:
                return f.read()
    return b''


def load_photo(directory: str, filename: str) -> str:
    """
    Загружает фото из выбранной директории и возвращает base64 в формате строки
    Параметры:
        directory: директория в папке media в которой находится фото
        filename: название фотки без расширения (передавать "photo_name", не "photo_name.jpg")
    Возвращает:
        Строку base64
        Если фото не найдено, вернёт пустоту ''

    Пример:
    >> load_photo('news_photo', '68')
    # загрузит фотографию 68.jpg из /media/news_photo/68.jpg
    """
    return base64.b64encode(load_file(directory, filename, ('.jpg', '.jpeg', '.png'))).decode('ascii')


def load_logo(directory: str, filename: str) -> str:
    """
    Загружает лого из выбранной директории и возвращает base64 в формате строки
    Параметры:
        directory: директория в папке media в которой находится лого
        filename: название фотки без расширения (передавать "photo_name", не "photo_name.jpg")
    Возвращает:
        Строку base64
        Если лого не найдено, вернёт пустоту ''

    Пример:
    >> load_logo('course_logo', '4')
    # загрузит логотип 4.svg из /media/course_logo/4.svg
    """
    return base64.b64encode(load_file(directory, filename, tuple(['.svg']))).decode('ascii')