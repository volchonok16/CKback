import base64

from flask import jsonify
from flask_restful import Resource
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time, load_logo


class InternshipRecent(Resource):
    """
    Модуль работы с курсами
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Выдаёт последние 3 по дате старте

        GET /api/internship/recent
        """
        query = f"""
            SELECT course_id, course_name, date_from actual_start_date, date_to actual_end_date
            FROM portal.t_courses_base
            ORDER BY date_from DESC LIMIT 3
        """
        result = self.db_worker.select_with_columns(query)
        for course in result:
            course['logo'] = load_logo('course_logo', str(course['course_id']))
            course['actual_start_date'] = strip_time(course['actual_start_date'])
            course['actual_end_date'] = strip_time(course['actual_end_date'])
        return jsonify(result)
