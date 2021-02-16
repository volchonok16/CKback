import os
import sys
import redis
import base64

from io import BytesIO

from pdf2image import convert_from_path

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker


class CertificatesMy(Resource):
    """
    Модуль работы с сертификатами
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Выдаёт все сертификаты пользователя по ИД пользователя

        GET /api/certificates/my
        """
        try: 
            email = self.redis_client.hget(request.headers['Authorization'], 'email').decode('utf-8')
        except (KeyError, AttributeError): # на случай если сессии нет в запросе
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})
        query = f"""
            SELECT certificate_name, certificate_path, certificate_id, portal.t_employee_base.employee_id
            FROM portal.t_employee_certificate
                LEFT JOIN portal.t_employee_base
                    ON portal.t_employee_base.employee_id = portal.t_employee_certificate.employee_id
            WHERE portal.t_employee_base.phoenix_email = '{email}'
        """
        poppler_path = os.path.join(os.getcwd(), 'src', 'utils', 'poppler', 'bin')
        result = self.db_worker.select_with_columns(query)
        for cert in result:
            buffered = BytesIO()
            cert_path = os.path.join("media", "user_certificates", str(cert['employee_id']), cert['certificate_path'])
            if sys.platform != 'linux':
                cert_photo = convert_from_path(cert_path, 150, poppler_path=poppler_path)[0] # 150 - параметр шакаливания (качества jpeg). Больше - лучше
            else:
                cert_photo = convert_from_path(cert_path, 150)[0]
            cert_photo.save(buffered, format="JPEG")
            cert['certificate'] = base64.b64encode(buffered.getvalue()).decode('ascii') # 1 - кол-во страниц для чтения
            del cert['certificate_path']
        return jsonify(result)
