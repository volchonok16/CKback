import os
import redis
import base64
import hashlib

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker


class Register(Resource):
    """
    Модуль регистрации пользователя
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def gen_salt(self) -> str:
        return base64.b64encode(os.urandom(64)).decode('utf-8')[:-2] # до -2 потому что последние два символа всегда "=="

    def post(self) -> Response:
        """
        Зарегистрировать пользователя
        """
        email = request.json.get('email')
        password = request.json.get('password')
        code = request.json.get('code')
        # проверка ввода пользователя
        try:
            str(email)
            assert "@" in email
            assert "." in email
            str(password)
            str(code)
        except (TypeError, ValueError, AssertionError): # проверка типа
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип: email должен быть string и содержать '@' и '.', password и code должны быть string."})
        try:
            code_ref = self.redis_client.get(email).decode('utf-8')
        except (KeyError, AttributeError):
            return jsonify({'status': 'warning', 'message': 'Код подтверждения не найден. Проверьте, правильно ли указан email.'})
        except AttributeError:
            return jsonify({'status': 'warning', 'message': 'Ваш код подтверждения истёк.'})
        if code != code_ref:
            return jsonify({'status': 'warning', 'message': 'Получен неправильный код подтверждения.'})
        # регистрируем пользователя
        salt = self.gen_salt()
        hashed_password = hashlib.sha512(password.encode('utf-8')+salt.encode('utf-8')).hexdigest()
        query = f"""
            SELECT employee_id
            FROM portal.t_employee_base
            WHERE phoenix_email = '{email}'
        """
        try:
            employee_id = self.db_worker.select(query)[0][0]
        except IndexError:
            return jsonify({'status': 'warning', 'message': "Пользователь с заданным email не найден в БД. Обратитесь к администратору."})
        command = f"""
            INSERT INTO portal.t_portal_auth
                (employee_id, password_hash, salt)
            VALUES
                ({employee_id}, '{hashed_password}', '{salt}');
        """
        done = self.db_worker.exec_command(command)
        if done:
            return jsonify({'status': 'success', 'message': "Пользователь зарегистрирован."})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД."})