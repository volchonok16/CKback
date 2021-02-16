import base64

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time, load_logo


class InternshipByMonth(Resource):
    """
    Модуль работы с внутренними стажировками
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Получение списка стажировок
        GET /api/internship/by_month?month={1-12}&is_inner=true
        {
            'coming': [
                {
                    id,
                    topic,
                    name,
                    duration: "{5 месяцев, 3 недели, 1 день}",
                    date_from,
                    date_to,
                    logo
                },
                ...
            ],
            'active': [
                ...
            ]
        }
        """

        parser = reqparse.RequestParser()
        parser.add_argument('month')
        parser.add_argument('is_inner')
        args = parser.parse_args()

        try:
            int(args['month'])
        except (TypeError, ValueError):
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, month должен быть int.'})

        query = f"""
                select course_id, course_name, topic, (date_to - date_from + 1) as duration,
                date_from as actual_start_date, date_from as actual_end_date 
                from portal.t_courses_base tc 
                where extract(month from date_from)={int(args['month'])}
                and date_to >= current_date 
                and date_from <= current_date
                and is_inner = {args['is_inner']}
                """

        query1 = f"""
                select course_id, course_name, topic, (date_to - date_from + 1) as duration,
                date_from as actual_start_date, date_from as actual_end_date
                from portal.t_courses_base tc 
                where extract(month from date_from)={int(args['month'])}
                and date_from>= current_date 
                and is_inner = {args['is_inner']}
                """

        result = self.db_worker.select_with_columns(query)
        result1 = self.db_worker.select_with_columns(query1)

        for course in result:
            course['logo'] = load_logo('course_logo', str(course['course_id']))
            course['actual_end_date'] = strip_time(course['actual_end_date'])
            course['actual_start_date'] = strip_time(course['actual_start_date'])

        for course in result1:
            course['logo'] = load_logo('course_logo', str(course['course_id']))
            course['actual_end_date'] = strip_time(course['actual_end_date'])
            course['actual_start_date'] = strip_time(course['actual_start_date'])

        return jsonify({'coming': result1, 'active': result})


