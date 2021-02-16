import redis
import base64

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import load_photo


class Me(Resource):
    """
    Профиль пользователя
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Краткая информация о себе
        GET /api/user/me
        {
            full_name
            photo
        }
        """
        # проверка что сессия есть в запросе
        try:
            email = self.redis_client.hget(request.headers['Authorization'], 'email').decode('utf-8')
        except (KeyError, AttributeError): # проверка типа
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})
        # получить employee_id пользователя из БД
        query = f"""
            SELECT employee_id, full_name
            FROM portal.t_employee_base
            WHERE phoenix_email = '{email}'
        """
        try:
            result = self.db_worker.select_with_columns(query)[0]
        except IndexError:
            return jsonify({'status': 'alert', 'message': 'Пользователь не найден в БД. Обратитесь к администратору.'})
        user_photo = load_photo('user_photo', str(result['employee_id']))
        return jsonify({'full_name': result['full_name'], 'photo': user_photo})
