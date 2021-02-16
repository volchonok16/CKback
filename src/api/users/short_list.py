from flask import jsonify
from flask_restful import Resource
from flask.wrappers import Response

from dbworker import DBWorker


class UsersShortList(Resource):
    """
    Модуль для работы с коротким списком пользователей
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Получение списка сотрудников в сокращенном виде

        GET /api/users/short_list
        [
            {
                id,
                full_name
            },
            ...
        ]
        """
        query = f"""
                    SELECT employee_id, full_name
                    FROM portal.t_employee_base
                """
        result = self.db_worker.select_with_columns(query)
        return jsonify(result)