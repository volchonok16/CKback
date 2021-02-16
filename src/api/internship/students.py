import base64
import os

from flask import jsonify
from flask_restful import Resource, reqparse
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time


class StudentInternshipStatus(Resource):
    """
    Статистика студента на стажировке
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Информация о стажировке
        GET /api/internship/students?id=

        (Резултат большой смотри документацию на конфе)
        """

        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            int(args['id'])
        except (TypeError, ValueError):  # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})

        query = f"""
                select course_name, 
                    teb.employee_id, 
                    full_name, 
                    comment 
                from portal.t_employee_base teb 
                    left join portal.t_employee_on_course teoc 
                        on teb.employee_id = teoc.employee_id 
                    left join portal.t_course_hist tch 
                        on teoc.course_hist_id = tch.course_hist_id
                    left join portal.t_courses_base tcb 
                        on tch.course_id = tcb.course_id 
                    where tcb.course_id = {args['id']}
                """


        result = self.db_worker.select_with_columns(query)

        users = []

        for user in result:
            users.append(user['employee_id'])

        print(users)

        hw_query = f"""
                select thb.homework_id, 
                        teb.employee_id, 
                        tfhp.score, 
                        tfhp.max_score, 
                        tl."name" 
                    from portal.t_employee_base teb 
                    left join portal.t_file_homework_progress tfhp 
                        on teb.employee_id = tfhp.employee_id 
                    left join portal.t_homeworks_base thb 
                        on tfhp.homework_id = thb.homework_id 
                    left join portal.t_lessons tl
                        on thb.lesson_id = tl.lesson_id 
                    left join portal.t_course_lessons tcl 
                        on tl.lesson_id = tcl.lesson_id 
                    left join portal.t_course_hist tch 
                        on tcl.course_hist_id = tch.course_hist_id 
                    left join portal.t_courses_base tcb 
                        on tch.course_id = tcb.course_id 
                    where tcb.course_id = {args['id']} and teb.employee_id in {tuple(users)}
                """

        test_query = f"""
                    select thb.homework_id, 
                        teb.employee_id, 
                        tl."name", 
                        ttp.correct_answers_num
                    from portal.t_employee_base teb 
                    left join portal.t_tests_progress ttp 
                        on teb.employee_id = ttp.employee_id 
                    left join portal.t_homeworks_base thb 
                        on ttp.homework_id = thb.homework_id 
                    left join portal.t_lessons tl
                        on thb.lesson_id = tl.lesson_id 
                    left join portal.t_course_lessons tcl 
                        on tl.lesson_id = tcl.lesson_id 
                    left join portal.t_course_hist tch 
                        on tcl.course_hist_id = tch.course_hist_id 
                    left join portal.t_courses_base tcb 
                        on tch.course_id = tcb.course_id 
                    where tcb.course_id = {args['id']}  and teb.employee_id in {tuple(users)}
"""

        result1 = self.db_worker.select_with_columns(hw_query)
        result2 = self.db_worker.select_with_columns(test_query)

        for user in result:
            user_photo = load_photo('user_photo', str(user['employee_id']))
            user['homework_list'] = []
            for homework in result1:
                if user['employee_id'] == homework['employee_id']:
                    user['homework_list'].append(homework)
            user['homework_count'] = len(user['homework_list'])

            user['test_list'] = []
            for test in result2:
                if user['employee_id'] == test['employee_id']:
                    user['test_list'].append(test)
            user['test_count'] = len(user['test_list'])

        return jsonify(result)
