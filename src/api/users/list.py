import os
import base64
import math


from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker


class UsersList(Resource):

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Список всех сотрудников
        GET /api/users/list?page=&size=&name=&skills={4,8}
        {
                total_pages: кол-во страниц,
                total_count: кол-во сотрудников,
                content: [
                        {
                            employee_id,
                            full_name,
                            photo,
                            position,
                            project,
                            manager
                        }
                ]
        }
        """

        parser = reqparse.RequestParser()
        parser.add_argument('size')
        parser.add_argument('page')
        parser.add_argument('name')
        parser.add_argument('skills')
        args = parser.parse_args()
        pagination = ''

        if args['size'] or args['page']:
            try:
                int(args['size'])
                int(args['page'])
                offset = int(args['size']) * (int(args['page']) - 1)
                pagination = f"LIMIT {args['size']} OFFSET {offset}"
            except (TypeError, ValueError):
                message = 'Получен некорректный тип. Size и page должны быть int.'
                return jsonify({'status': 'warning', 'message': message})

        skills = args['skills'].split(',')
        # TODO: проверка
        children = ''
        if args['name']:
            children = children + f""" and lower(e.full_name) like lower('%{args['name']}%')"""
        if args['skills']:
            children = children + f""" and tsd.skill_id in ({(', '.join(skills))})"""

        # TODO: переписать запросик на кол-во
        query = f"""SELECT distinct e.employee_id,
                        e.full_name, 
                        e."position",
                        (select z.full_name from  portal.t_employee_base z where  z.employee_id = e.leader_id) as manager
                    FROM portal.t_employee_base e 
                        left join portal.t_employee_skills tes on e.employee_id = tes.employee_id
                        left join portal.t_skills_dim tsd on tes.skill_id = tsd.skill_id
                    where 1=1        
                """ + children + ' ' + pagination

        query_c = f"""select count(1) as cnt 
                    FROM (SELECT distinct e.employee_id,
                        e.full_name, 
                        e."position",
                        (select z.full_name from  portal.t_employee_base z where  z.employee_id = e.leader_id) as manager
                    FROM portal.t_employee_base e 
                        left join portal.t_employee_skills tes on e.employee_id = tes.employee_id
                        left join portal.t_skills_dim tsd on tes.skill_id = tsd.skill_id
                    where 1=1
                        {children}) as t
                    """

        result = self.db_worker.select_with_columns(query)

        try:
            count = self.db_worker.select_with_columns(query_c)[0]['cnt']
        except IndexError:
            count = 0

        for user in result:
            user_photo = load_photo('user_photo', str(user['employee_id']))

        pages = math.ceil(count / int(args['size']))
        # result = ['total_pages: ' + str(math.ceil(count / int(args['size']))), 'total_count: ' + str(count)] + result

        return jsonify({'total_count': count, 'total_pages': pages, 'users': result})
