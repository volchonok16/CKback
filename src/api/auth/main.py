import uuid
import redis
import base64
import hashlib
import ipaddress

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker


class Auth(Resource):
    """
    Работа с авторизацией
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def post(self) -> Response:
        """
        Логинит пользователя в систему
        Создаёт новую сессию
        """
        email = request.json.get('email')
        password = request.json.get('password')
        # проверка ввода пользователя
        try:
            str(email)
            assert "@" in email
            assert "." in email
            str(password)
        except (TypeError, ValueError, AssertionError): # проверка типа
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип: email должен быть string и содержать '@' и '.', password должен быть string."})
        # проверить что пользователь есть в базе
        query = f"""
            SELECT
                portal.t_employee_base.employee_id,
                portal.t_portal_auth.password_hash,
                portal.t_portal_auth.salt,
                portal.t_portal_auth.login_failed_count 
            FROM portal.t_employee_base
                LEFT JOIN portal.t_portal_auth
                    ON portal.t_employee_base.employee_id = portal.t_portal_auth.employee_id
            WHERE
                portal.t_employee_base.phoenix_email = '{email}'
                AND
                portal.t_portal_auth.end_date > now()
        """
        try:
            data = self.db_worker.select(query)[0]
            employee_id = data[0]
            password_ref = data[1]
            salt = data[2]
            count_failed = data[3]
        except IndexError:
            return jsonify({'status': 'warning', 'message': "Пользователь с заданным e-mail и паролем не найден в БД. Пожалуйста, зарегистрируйтесь."})
        # проверить что кол-во неуспешных попыток не больше 5
        if count_failed >= 5:
            return jsonify({'status': 'alert', 'message': "Слишком много неудачных попыток входа."})
        # проверить что пароль совпадает
        hashed_password = hashlib.sha512(password.encode('utf-8')+salt.encode('utf-8')).hexdigest()
        if hashed_password != password_ref:
            # увеличить счётчик неуспешных попыток на +1
            command = f"""
                UPDATE portal.t_portal_auth
                SET login_failed_count = {count_failed+1}
                WHERE employee_id = {employee_id} AND end_date > now()
            """
            done = self.db_worker.exec_command(command)
            if not done:
                return jsonify({'status': 'alert', 'message': "Ошибка записи в БД. Обратитесь к администратору."})
            return jsonify({'status': 'warning', 'message': "Неправильный e-mail и/или пароль."})
        # создать сессию
        session = str(uuid.uuid4())
        # положить в базу и обнулить счётчик неуспешных попыток входа
        command = f"""
            UPDATE portal.t_portal_auth
            SET login_failed_count = 0
            WHERE employee_id = {employee_id} AND end_date > now();
        """
        self.redis_client.hset(session, "email", email)
        self.redis_client.hset(session, "employee_id", employee_id)
        self.redis_client.expire(session, 86_400) # 86_400 - 24 часа в секундах
        done = self.db_worker.exec_command(command)
        if not done:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД. Обратитесь к администратору."})
        return jsonify({'status': 'success', 'message': 'Авторизация успешна.', 'Authorization': session})

    def delete(self) -> Response:
        """
        Закрывает сессию пользователя
        """
        try:
            done = self.redis_client.delete(request.headers['Authorization'])
        except KeyError:
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией.'})
        if done:
            return jsonify({'status': 'success', 'message': 'Вы вышли из системы.'})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД. Обратитесь к администратору."})