import os
import uuid
import redis

from flask import jsonify, send_file
from flask_restful import Resource, reqparse
from flask.wrappers import Response

from dbworker import DBWorker


class FilesCourseContents(Resource):
    """
    Стажировка
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Получить файл
        GET /api/files/course_contents?filename=&key=
        """
        parser = reqparse.RequestParser()
        parser.add_argument('filename')
        parser.add_argument('key')
        args = parser.parse_args()
        try:
            str(args['filename'])
            assert len(args['filename']) > 0
            uuid.UUID(args['key'], version=4)
        except (TypeError, ValueError, AssertionError):
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, filename должен быть string, key должен быть uuid.'})
        path = os.path.join(os.getcwd(), 'media', 'course_contents', args['key'])
        return send_file(path, as_attachment=True, attachment_filename=args['filename'])