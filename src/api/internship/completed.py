import redis
import base64

from flask import jsonify
from flask_restful import Resource, request
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time, load_logo


class InternshipCompleted(Resource):
    """
    Модуль работы с курсами
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Выдаёт информацию по активным курсам пользователя
        GET /api/internship/active
        """
        # вытаскиваем email пользователя, который зашёл на страницу, через его сессию
        # redis хранит связь сессия - email пользователя
        try: 
            email = self.redis_client.hget(request.headers['Authorization'], 'email').decode('utf-8')
        except (KeyError, AttributeError): # на случай если сессии нет в запросе
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})
        query = f"""
            SELECT
                t_courses_base.course_id,
                t_courses_base.course_name,
                t_courses_base.date_from actual_start_date,
                t_courses_base.date_to actual_end_date
            FROM portal.t_employee_base
                LEFT JOIN portal.t_course_student
                    ON portal.t_course_student.employee_id = portal.t_employee_base.employee_id 
                LEFT JOIN portal.t_courses_base
                    ON portal.t_course_student.course_id = portal.t_courses_base.course_id
            WHERE t_employee_base.phoenix_email = '{email}'
                AND t_course_student.is_completed = true
        """
        result = self.db_worker.select_with_columns(query)
        for course in result:
            course['logo'] = load_logo('course_logo', str(course['course_id']))
            course['actual_start_date'] = strip_time(course['actual_start_date'])
            course['actual_end_date'] = strip_time(course['actual_end_date'])
        return jsonify(result)
