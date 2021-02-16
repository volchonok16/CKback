from flask import jsonify
from flask_restful import Resource, reqparse
from flask.wrappers import Response

from dbworker import DBWorker


class StudentsShortList(Resource):
    """
    Модуль для работы с коротким списком студентов
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Получение списка сотрудников в сокращенном виде

        GET /api/internship/list_students?id=
        [
            {
                id,
                full_name
            },
            ...
        ]
        """

        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            int(args['id'])
        except (TypeError, ValueError):  # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})

        query = f"""
                    SELECT teb.employee_id, 
                    teb.full_name
                        FROM portal.t_employee_base teb 
                        left join portal.t_employee_on_course teoc 
                            on teb.employee_id = teoc.employee_id 
                        left join portal.t_course_hist tch 
                            on teoc.course_hist_id = tch.course_hist_id 
                        left join portal.t_courses_base tcb 
                            on tch.course_id = tcb.course_id
                        where tcb.course_id = {args['id']}

                """

        result = self.db_worker.select_with_columns(query)
        return jsonify(result)
