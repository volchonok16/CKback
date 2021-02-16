import redis

from flask import request

from werkzeug.exceptions import Unauthorized

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker


class Sentry:
    """
    Объект защиты системы.
    Black- и whitelist'ы, обновление сессии, проверка роли пользователя - всё здесь.
    1. Проверяет что пользователь авторизован
    2. Обновляет сессию пользователя
    """

    def __init__(self, req: request, redis_client: redis.Redis) -> None:
        # self.db_worker = db_worker
        self.req = req
        self.redis_client = redis_client
        if self.check_auth():
            self.renew_session()
        else:
            raise Unauthorized()

    def check_auth(self) -> bool:
        # проверить что пользователь залогинен
        try:
            if self.redis_client.hget(self.req.headers['Authorization'], "employee_id"):
                return True
        except (KeyError, redis.RedisError):
            return False

    def renew_session(self) -> None:
        self.redis_client.expire(self.req.headers['Authorization'], 86_400) # 86_400 - 24 часа в секундах