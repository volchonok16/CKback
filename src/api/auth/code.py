import redis
import string
import random
import smtplib

from email.message import EmailMessage

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker


class Code(Resource):
    """
    Модуль работы с кодом подтверждения электронной почты (email)
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def gen_code(self) -> str:
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def get(self) -> Response:
        """
        Отправить код подтверждения
        """
        parser = reqparse.RequestParser()
        parser.add_argument('email')
        args = parser.parse_args()
        # проверка ввода пользователя
        try:
            email = str(args['email'])
            assert "@" in email
            assert "." in email
        except (TypeError, ValueError, AssertionError): # проверка типа
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип, email должен быть string и содержать '@' и '.'."})
        try:
            code = self.gen_code()
            self.redis_client.set(email, code, ex=300) # ex = expire, срок жизни кода
        except redis.RedisError:
            return jsonify({'status': 'alert', 'message': 'Ошибка связи с Redis.'})
        try:
            server = smtplib.SMTP("192.168.199.112", 25)
            msg = EmailMessage()
            msg['Subject'] = 'Код подтверждения электронной почты'
            msg['From'] = 'ckportal@notify-service.info'
            msg['To'] = email
            msg.set_content("Ваш код подтверждения: " + code)
            server.send_message(msg)
            return jsonify({'status': 'success', 'message': 'Код подтверждения отправлен на указанную электронную почту.'})
        except:
            return jsonify({'status': 'alert', 'message': 'Ошибка отправки кода подтверждения.'})