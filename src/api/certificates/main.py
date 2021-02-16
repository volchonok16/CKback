import os
import base64

from io import BytesIO

from pdf2image import convert_from_path

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker


class CertificatesMain(Resource):
    """
    Модуль работы с сертификатами
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def post(self) -> Response:
        """
        Загружает новый сертификат
        Сохраняет в папку /media/user_certificates/ИД_пользователя/

        POST /api/certificates
        """
        cert_desc = request.form.get('cert_desc')
        # проверка ввода пользователя
        try:
            str(cert_desc)
            assert request.files['certificate'].filename.split('.')[-1] == 'pdf'
        except (TypeError, ValueError, AssertionError): # проверка типа
            message = 'Получен некорректный тип. User_id должен быть int, cert_desc должен быть str, certificate (файл) должен быть в формате pdf.'
            return jsonify({'status': 'warning', 'message': message})
        try:
            user_id = self.redis_client.hget(request.headers['Authorization'], "employee_id").decode('utf-8')
        except (KeyError, AttributeError):
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})
        # сохраняем файл
        certs_dir = os.path.join('media', 'user_certificates', user_id)
        cert_path = os.path.join(certs_dir, request.files['certificate'].filename)
        if not os.path.isfile(cert_path):
            request.files['certificate'].save(cert_path)
            filename = request.files['certificate'].filename
        else:
            split_path = cert_path.split('.')
            split_name = request.files['certificate'].filename.split('.')
            name_wo_ext = request.files['certificate'].filename.split('.')[0]
            copy_number = 1 # начинаем с 1 т.к. у нас уже есть одна копия
            for filename in os.listdir(certs_dir):
                copy_number += 1 if name_wo_ext in filename else 0
            number_str = f'_{copy_number}.'
            cert_path = split_path[-2] + number_str + split_path[-1]
            filename = split_name[-2] + number_str + split_name[-1]
            request.files['certificate'].save(cert_path)
        # записываем новый сертификат в базе
        query = f"""
            INSERT INTO portal.t_employee_certificate
            (employee_id, certificate_name, certificate_path)
            VALUES({user_id}, '{cert_desc}', '{filename}');
        """
        done = self.db_worker.exec_command(query)
        if not done:
            return jsonify({'status': 'alert', 'message': 'Ошибка записи в БД. Обратитесь к администратору'})
        return jsonify(success=True)

    def delete(self) -> Response:
        """
        Удаляет загруженный сертификат из папки
        /media/user_certificates/{ИД_пользователя}/{название_сертификата}

        DELETE /api/certificates?id=
        """        
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        # проверка ввода пользователя
        try:
            int(args['id'])
        except (TypeError, ValueError): # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})
        # получить id пользователя и название сертификата из БД
        query = f"SELECT employee_id, certificate_path FROM portal.t_employee_certificate WHERE certificate_id = {args['id']}"
        result = self.db_worker.select_with_columns(query)
        if not result:
            return jsonify({'status': 'warning', 'message': 'Заданный сертификат не найден.'})
        else:
            employee_id = result[0].get('employee_id')
            cert_name = result[0].get('certificate_path')
        # удаляем файл
        certs_dir = os.path.join('media', 'user_certificates', str(employee_id))
        cert_path = os.path.join(certs_dir, cert_name)
        if not os.path.isfile(cert_path):
            return jsonify({'status': 'alert', 'message': 'Файл сертификата не найден на сервере. Обратитесь к администратору.'})
        else:
            os.remove(cert_path)
        command = f"DELETE FROM portal.t_employee_certificate WHERE certificate_id = {args['id']} RETURNING 1"
        result = self.db_worker.exec_command(command)
        if not result:
            return jsonify({'status': 'alert', 'message': 'Ошибка удаления записи из БД. Обратитесь к администратору.'})
        else:
            return jsonify({'status': 'success', 'message': 'Сертификат удалён.'})