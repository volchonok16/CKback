import os
import uuid
import json

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time

from datetime import datetime


class InternshipLessons(Resource):
    """
    Модуль работы с уроками стажировки
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def post(self) -> Response:
        """
        Загрузка новых уроков
        POST /api/internship/lessons?internship_id=
        """
        parser = reqparse.RequestParser()
        parser.add_argument('internship_id')
        args = parser.parse_args()
        data = json.loads(request.files.get('json').read())
        # сохранить полученные файлы в папку course_contents, присвоить file_key
        for lesson in data['lessons']:
            mats = lesson['materials']
            for file in mats['videos'] + mats['files']:
                file_key = uuid.uuid4()
                request.files[file['filename']].save(os.path.join('media', 'course_contents', str(file_key)))
                file['file_key'] = str(file_key)
        # загрузить уроки
        command = f"""
                UPDATE portal.t_courses_base
                SET lessons_json='{str(data['lessons']).replace("'", "''")}'
                WHERE course_id={args['internship_id']}
        """
        done = self.db_worker.exec_command(command)
        if not done:
            return jsonify({'status': 'alert', 'message': 'Ошибка добавления уроков в БД. Обратитесь к администратору.'})
        return jsonify({'status': 'success', 'message': 'Уроки добавлены в стажировку.'})