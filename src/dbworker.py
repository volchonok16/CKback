import logging
import psycopg2


class DBWorker:
    """
    Класс работы с базой данных
    """
    
    def __init__(self, config: dict) -> None:
        logging.debug('Инициализация DBWorker.')
        self.config = config
        self.test_connection()

    def test_connection(self) -> bool:
        """
        Проверяет соединение с базой
        Возвращает True если соединение есть
        Возвращает False если нет
        Не вижу смысла выносить эту функцию в тесты
        """
        with psycopg2.connect(**self.config['database']) as conn:
            result = conn.closed
        if not result:
            logging.debug(f"Есть подключение к базе {self.config['database']['dbname']}.")
        else:
            logging.critical(f'Нет подключения к базе. Проверьте конфиг.')
        return not result

    def exec_command(self, command: str) -> bool:
        """
        Выполняет SQL команду и применяет внесенные изменения
        Если команду невозможно выполнить по какой-либо причине, изменения откатываются
        Возвращает True если команда выполнена успешно
        """
        with psycopg2.connect(**self.config['database']) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(command)
                    conn.commit()
                    done = True
                except Exception as e:
                    conn.rollback()
                    message = f'Невозможно выполнить команду\n{command}\n{str(e)}\nОткатываем изменения.'
                    logging.critical(message)
                    done = False
        return done

    def exec_returning(self, command: str) -> tuple:
        """
        Выполняет SQL команду с возвратом (например, RETURNING id)
        Применяет внесенные изменения
        Если команду невозможно выполнить по какой-либо причине, изменения откатываются
        """
        with psycopg2.connect(**self.config['database']) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(command)
                    data = cur.fetchone()
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    message = f'Невозможно выполнить команду с возвратом\n{command}\n{str(e)}\nОткатываем изменения.'
                    logging.critical(message)
                    data = ()
        return data

    def select(self, command: str) -> list:
        """
        Метод для работы с простым SELECT
        Отличается от exec_command тем, что никакие изменения не применяются
        Возвращает массив с данными
        """
        with psycopg2.connect(**self.config['database']) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(command)
                    data = cur.fetchall()
                except Exception as e:
                    message = f'Невозможно выполнить запрос\n{command}\n{str(e)}'
                    logging.critical(message)
        return data

    def select_with_columns(self, command: str) -> list:
        """
        Вытаскивает всю информацию из заданной таблицы
        Превращает в массив словарей для дальнейшей трансформации в json

        Пример:
            [('reg_number',), ('date_created',), ('status',), ('source',), ('project',), ('data_volume',)]
            [(4, datetime.datetime(2020, 9, 9, 19, 20, 32, 261269), 0, 'Источник', '1 Проект', 'Стандартная')]

        Трансформируется в:
            [
              {
                "data_volume": "Стандартная", 
                "date_created": "Wed, 09 Sep 2020 19:20:32 GMT", 
                "project": "1 Проект", 
                "reg_number": 4, 
                "source": "Источник", 
                "status": 0
              }
            ]
        """
        with psycopg2.connect(**self.config['database']) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(command)
                    data = cur.fetchall()
                    columns = cur.description
                    result = [dict(zip([c[0] for c in columns], item)) for item in data]
                except Exception as e:
                    message = f'Невозможно выполнить запрос\n{command}\n{str(e)}'
                    logging.critical(message)
                    result = []
        return result

    def call_func(self, function: str, params: list) -> tuple:
        """
        Осуществляет вызов функции в базе данных.
        """
        with psycopg2.connect(**self.config['database']) as conn:
            with conn.cursor() as cur:
                try:
                    cur.callproc(function, params)
                    data = cur.fetchall()
                except Exception as e:
                    message = f'Невозможно запустить функцию\n{function}\n{str(e)}'
                    logging.critical(message)
                    data = str(e)
        return data