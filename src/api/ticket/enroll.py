import redis

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker

class SighUpInternship(Resource):

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def post(self) -> Response:
        """
        Кнопка записаться на стажировку
        POST /api/ticket/enroll
        """
        internship_id = request.json('internship_id')

        try:
            int(internship_id)
        except (TypeError, ValueError):  # проверка типа
            return jsonify({'status': 'warning',
                            'message': 'Получен некорректный тип, user_id и internship_id должны быть int.'})

        try:
            employee_id = self.redis_client.hget(request.headers['Authorization'], "employee_id").decode('utf-8')
        except (KeyError, AttributeError):
            return jsonify({'status': 'warning',
                            'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})

        command = f"""
                INSERT INTO portal.portal.t_course_student
                (employee_id, course_id)
                VALUES({employee_id}, {internship_id});
                """

        done = self.db_worker.exec_command(command)

        if done:
            return jsonify({'status': 'success', 'message': "Пользователь зарегистрирован на стажировку."})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД."})
