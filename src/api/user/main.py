import base64

from flask import jsonify
from flask_restful import Resource, reqparse
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import load_photo


class User(Resource):
    """
    Профиль пользователя
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Полная информация о пользователе
        GET /api/user?id=
        {
            id,
            first_name,
            second_name,
            last_name,
            job,
            intranet_email,
            corp_email,
            skills: "Java, Python"
        }
        """
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        # проверка ввода пользователя
        try:
            int(args['id'])
        except (TypeError, ValueError): # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})
        user_photo = load_photo('user_photo', str(args['id']))
        query = f"""
            select 
             distinct 
              teb.employee_id
              , teb.full_name
              , teb.phoenix_email
              , teb.corp_email
              , teb.position
              , string_agg(tsd.skill_name, ', ')  over(partition by tes.employee_id) skills   


            from portal.t_employee_base teb 
              left join  portal.t_employee_skills tes
                on teb.employee_id = tes.employee_id 
              left join portal.t_skills_dim tsd 
                on tes.skill_id = tsd.skill_id
            WHERE teb.employee_id = {args['id']}
        """
        try:
            result = self.db_worker.select_with_columns(query)[0]
            result['photo'] = user_photo
        except IndexError: # если не найден пользователь в базе
            result = {}
        return jsonify(result)
