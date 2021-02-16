import json
import logging


def parse(path_to_file: str) -> dict:
    """
    Парсит JSON конфиг
    Возвращает словарь {раздел: {логин: "", пароль: "", ...}, ...}
    """
    with open(path_to_file, 'r', encoding='utf-8') as f:
        config = json.loads(f.read())
        logging.debug('Считываем настройки из файла config.json.')
    return config
