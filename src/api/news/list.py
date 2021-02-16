import os
import base64

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker
from utils.functions import load_photo


class NewsList(Resource):
    """
    Модуль работы с новостями
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Выдаёт последние новости
        GET /api/news?size=3&page=1
        {
            title (нет в БД, не выдаёт)
            content
            photo
            date
        }
        """
        parser = reqparse.RequestParser()
        parser.add_argument('size')
        parser.add_argument('page')
        args = parser.parse_args()
        pagination = ''
        # проверка ввода пользователя не проводится в обязательном порядке
        # т.к. может быть необходимо получить весь список новостей
        if args['size'] or args['page']:
            try:
                int(args['size'])
                int(args['page'])
                offset = int(args['size'])*(int(args['page'])-1)
                pagination = f"LIMIT {args['size']} OFFSET {offset}"
            except (TypeError, ValueError): # проверка типа
                message = 'Получен некорректный тип. Size и page должны быть int.'
                return jsonify({'status': 'warning', 'message': message})
        query = f"""
            SELECT
                portal.t_employee_base.full_name author,
                portal.t_news.news_text "content",
                portal.t_news.insert_date "date",
                portal.t_news.news_title "title",
                portal.t_news.news_id,
                count(*) OVER() AS total_count
            FROM portal.t_news
                LEFT JOIN portal.t_employee_base
                    ON portal.t_news.creator_id = portal.t_employee_base.employee_id
        """ + pagination

        result = self.db_worker.select_with_columns(query)
        try:
            count = result[0]['total_count']
        except IndexError:
            count = 0

        for news in result:
            news['photo'] = load_photo('news_photo', str(news['news_id']))
        return jsonify({'total_news': count, 'news': result})
