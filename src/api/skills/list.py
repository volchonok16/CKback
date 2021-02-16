from flask import jsonify
from flask_restful import Resource
from flask.wrappers import Response

from dbworker import DBWorker


class SkillsList(Resource):
    """
    Модуль для работы с коротким списком пользователей
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Получение списка навыков
        GET /api/skills/list
        [
            {
                id,
                name
            },
            ...
        ]
        """
        query = f"""
                    SELECT skill_id, skill_name
                    FROM portal.t_skills_dim
                """
        result = self.db_worker.select_with_columns(query)
        return jsonify(result)