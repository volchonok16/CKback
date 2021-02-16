import uuid
import json
import redis

from flask import jsonify
from flask_restful import Resource, request, reqparse
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time, load_logo


class TestsMain(Resource):
    """
    Модуль работы с тестами
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def post(self) -> Response:
        """
        Загрузка нового теста
        POST api/tests
        """
        # сформатировать sql запрос
        try:
            course_id = request.json['course_id']
            pass_score = request.json['pass_score']
            lesson_uid = uuid.UUID(request.json['lesson_uid'])
            values = []
            for question in request.json['questions']:
                for answer_id, answer in enumerate(question['answers'], 1):
                    values.append(f"({course_id}, '{lesson_uid}', {question['id']}, {answer_id}, '{question['body']}', '{answer['body']}', {answer['is_correct']}, {pass_score}),\n")
        except (ValueError, KeyError, TypeError):
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип данных. Обратитесь к документации."})

        command = f"""
            BEGIN;
                DELETE FROM portal.t_tests_base
                    WHERE lesson_uid='{lesson_uid}';

                INSERT INTO portal.t_tests_base
                    (course_id, lesson_uid, question_id, answer_id, question_text, answer_text, is_correct, pass_score)
                VALUES
                    {''.join(values)[:-2]};
            COMMIT;
        """
        # отправить в базу
        done = self.db_worker.exec_command(command)
        # вернуть ответ
        if done:
            return jsonify({'status': 'success', 'message': "Добавлен новый тест."})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД. Обратитесь к администратору."})

    def delete(self) -> Response:
        """
        Удаление теста по lesson_uid
        DELETE api/tests?uid=
        """
        parser = reqparse.RequestParser()
        parser.add_argument('uid')
        args = parser.parse_args()
        try:
            lesson_uid = uuid.UUID(args['uid'])
        except ValueError:
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип данных, uid должен быть в формате UUID и указывать на урок, тест которого необходимо удалить."})

        command = f"""DELETE FROM portal.t_tests_base WHERE lesson_uid='{lesson_uid}';"""
        # отправить в базу
        done = self.db_worker.exec_command(command)
        # вернуть ответ
        if done:
            return jsonify({'status': 'success', 'message': f"Тест uid={lesson_uid} удалён."})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД. Обратитесь к администратору."})