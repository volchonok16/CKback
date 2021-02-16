import redis

from flask import jsonify
from flask_restful import Resource, request, reqparse
from flask.wrappers import Response

from dbworker import DBWorker

from datetime import datetime


class TicketCreateInternship(Resource):
    """
    Заявка на создание стажировки
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Выдача заявки
        GET /api/ticket/create_internship?id=
        """
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            int(args['id'])
        except (TypeError, ValueError, AssertionError):  # проверка типа
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип данных, id должен быть int."})
        query = f"""
            SELECT *
            FROM portal.t_course_ticket_create
            WHERE id = {args['id']}
        """
        try:
            result = self.db_worker.select_with_columns(query)[0]
            return jsonify(result)
        except IndexError:
            return jsonify({'status': 'warning', 'message': f"Заявка с id={args['id']} не найдена."})

    def post(self) -> Response:
        """
        Создание заявки
        POST /api/ticket/create_internship
        {
            "is_inner": true/false,
            "is_online": true/false,
            "skills": ["Java", "Python", ...],
            "date_from": "10.03.2020",
            "date_to": "10.03.2020",
            "students_num": 17,
            "requirements": "Текст, текст, текст, ..."
        }
        """
        is_inner = request.json.get('is_inner')
        is_online = request.json.get('is_online')
        skills = request.json.get('skills')
        date_from = request.json.get('date_from')
        date_to = request.json.get('date_to')
        students_num = request.json.get('students_num')
        requirements = request.json.get('requirements')
        try:
            assert isinstance(is_inner, bool)
            assert isinstance(is_online, bool)
            list(skills)
            datetime.strptime(date_from, '%m.%d.%Y')
            datetime.strptime(date_to, '%m.%d.%Y')
            int(students_num)
            str(requirements)
        except (TypeError, ValueError, AssertionError):  # проверка типа
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип данных. Обратитесь к документации."})
        try:
            employee_id = self.redis_client.hget(request.headers['Authorization'], "employee_id").decode('utf-8')
        except (KeyError, AttributeError):
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})

        command = f"""
            INSERT INTO portal.t_course_ticket_create
                (skills, is_online, is_inner, date_from, date_to, students_num, requirements, creator_id)
            VALUES
                ('{', '.join(skills)}', {is_online}, {is_inner}, '{date_from}', '{date_to}', {students_num}, '{requirements}', {employee_id});
        """
        done = self.db_worker.exec_command(command)
        if done:
            return jsonify({'status': 'success', 'message': "Создана заявка на проведение стажировки."})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД."})