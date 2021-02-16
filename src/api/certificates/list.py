import os
import sys
import base64

from io import BytesIO

from pdf2image import convert_from_path

from flask import jsonify
from flask_restful import Resource, reqparse
from flask.wrappers import Response

from dbworker import DBWorker


class CertificatesList(Resource):
    """
    Модуль работы с сертификатами
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Выдаёт все сертификаты пользователя по ИД пользователя

        GET /api/certificates/list
        [
            {
                certificate
                certificate_name
            }
        ]
        """
        parser = reqparse.RequestParser()
        parser.add_argument('user_id')
        args = parser.parse_args()
        # проверка ввода пользователя
        try:
            int(args['user_id'])
        except (TypeError, ValueError): # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, user_id должен быть int.'})
        query = f"""
            SELECT certificate_name, certificate_path, certificate_id
            FROM portal.t_employee_certificate
            WHERE employee_id = {args['user_id']}
        """
        poppler_path = os.path.join(os.getcwd(), 'src', 'utils', 'poppler', 'bin')
        result = self.db_worker.select_with_columns(query)
        for cert in result:
            buffered = BytesIO()
            cert_path = os.path.join("media", "user_certificates", args['user_id'], cert['certificate_path'])
            if sys.platform != 'linux':
                cert_photo = convert_from_path(cert_path, 150, poppler_path=poppler_path)[0] # 150 - параметр шакаливания (качества jpeg). Больше - лучше
            else:
                cert_photo = convert_from_path(cert_path, 150)[0]
            cert_photo.save(buffered, format="JPEG")
            cert['certificate'] = base64.b64encode(buffered.getvalue()).decode('ascii') # 1 - кол-во страниц для чтения
            del cert['certificate_path']
        return jsonify(result)
