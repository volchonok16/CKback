import os
import redis
import json
import uuid

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker


class Homework(Resource):
    """
    Домашние работы
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Информация о домашке
        GET /api/internship/homework?key=

        (Резултат большой смотри документацию на конфе)
        """

        parser = reqparse.RequestParser()
        parser.add_argument('key')
        args = parser.parse_args()
        try:
            uuid.UUID(args['key'], version=4)
        except (TypeError, ValueError): # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})

        query = f'''
                select thp.course_id,
                    thp.employee_id,
                    thp.mentor_comment,
                    thp.score,
                    tcb.lessons_json
                    from portal.t_homework_progress thp
                    inner join portal.t_courses_base tcb
                    on thp.course_id = tcb.course_id 
                    where thp.test_uid = {uuid.UUID(args['key'], version=4)}
                '''

        result = self.db_worker.select_with_columns(query)

        lessons = json.loads(fr'''{result[0]['lessons_json']}'''.replace('\'', '\"'))

        for lesson in lessons:
            if lesson['lesson_id'] == int(args['homework_id']):
                result[0]['homework_desc'] = lesson['homework']

        del result[0]['lessons_json']
        # TODO: вытаскивать файл с домашкой (поговорить с Саней)
        return jsonify(result[0])

    def put(self) -> Response:
        """
        Загрузка комментария ментора.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('key')
        args = parser.parse_args()
        mentor_comment = request.form.get('mentor_comment')
        score = request.form.get('score')


        try:
            uuid.UUID(args['key'], version=4)
            int(score)
        except (TypeError, ValueError):  # проверка типа
            return jsonify({'status': 'warning',
                            'message': 'Получен некорректный тип, user_id и internship_id должны быть int.'})

        try:
            mentor_id = self.redis_client.hget(request.headers['Authorization'], "employee_id").decode('utf-8')
        except (KeyError, AttributeError):
            return jsonify({'status': 'warning',
                            'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})

        command = f"""
                    UPDATE portal.t_homework_progress
                        SET  mentor_comment={mentor_comment}, score={score}, mentor_id={mentor_id}
                    WHERE test_uid = {uuid.UUID(args['key'], version=4)} ;

                        """

        done = self.db_worker.exec_command(command)
        if not done:
            return jsonify({'status': 'alert', 'message': 'Ошибка записи в БД. Обратитесь к администратору'})