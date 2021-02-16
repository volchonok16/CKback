import os
import uuid
import base64

from flask import jsonify
from flask_restful import Resource, reqparse
from flask.wrappers import Response
from collections import defaultdict
from dbworker import DBWorker
from utils.functions import strip_time, load_photo


class InternshipTake(Resource):
    """
    Страница прохождения курса
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Выдаёт информацию для прохождения выбранной стажировки
        GET /api/internship/take?id=
        """
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            int(args['id'])
        except (TypeError, ValueError):
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})
        query = f"""
            SELECT
                t_courses_base.course_id,
                course_name,
                date_from,
                date_to,
                skills,
                description,
                target_audience_desc,
                lessons_json,
                string_agg(portal.t_employee_base.full_name, ', ') mentors,
                string_agg(portal.t_employee_base.employee_id::varchar, ', ') mentors_ids
            FROM portal.t_courses_base
                LEFT JOIN portal.t_course_mentors
                    ON portal.t_course_mentors.course_id = portal.t_courses_base.course_id
                LEFT JOIN portal.t_employee_base
                    ON portal.t_employee_base.employee_id = portal.t_course_mentors.employee_id
            WHERE portal.t_courses_base.course_id = {args['id']}
            GROUP BY
                (t_courses_base.course_id)
        """
        result = self.db_worker.select_with_columns(query)
        if not len(result):
            return jsonify({'status': 'warning', 'message': 'Заданная стажировка не найдена.'})
        # формируем менторов - нужен employee_id, full_name и photo
        mentors = []
        # получаем их id и имена из запроса (они идут через запятую и пробел)
        try:
            mentors_list = result[0].get('mentors').split(', ')
            mentors_ids = result[0].get('mentors_ids').split(', ')
        except AttributeError:
            mentors_list = []
            mentors_ids = []
        # одновременно проходим по двум полученным массивам
        for mentor_id, mentor_name in zip(mentors_ids, mentors_list):
            photo = load_photo('user_photo', str(mentor_id))
            mentors.append({'employee_id': int(mentor_id), 'full_name': mentor_name, 'photo': photo})
        try:
            lessons = eval(result[0].get('lessons_json').replace('\n', '\\n'))
        except SyntaxError:
            lessons = []
        course_info = {
            'course_name': result[0].get('course_name'),
            'date_from': strip_time(result[0].get('date_from')),
            'date_to': strip_time(result[0].get('date_to')),
            'mentors': mentors,
            'lessons_json': lessons
        }
        return jsonify(course_info)
