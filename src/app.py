import redis
import argparse

from utils import config_parser
from dbworker import DBWorker
from api.api_start import run_server


def parse_args() -> argparse.Namespace:
    """
    Парсит входные агрументы
    """
    parser = argparse.ArgumentParser(description='Backend сервер портала Центра Компетенций.')
    parser.add_argument('--s', '--start', help='Запустить сервер', action='store_true')
    return parser.parse_args()


def start(config: dict, db_worker: DBWorker, redis_client: redis.Redis) -> None:  
    """
    Запускает сервер с параметрами из конфига
    """
    run_server(config, db_worker, redis_client)


def main() -> None:
    config = config_parser.parse('config.json')
    db_worker = DBWorker(config)
    redis_client = redis.Redis(password=config['redis_pass'])
    try:
        redis_client.get('1')
    except redis.exceptions.ConnectionError:
        print('Ошибка подключения к Redis.')
        exit()
    args = parse_args()

    if args.s: # запуск
        start(config, db_worker, redis_client)


if __name__ == '__main__':
    main()