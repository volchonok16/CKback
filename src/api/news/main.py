import os
import base64

from datetime import datetime

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker
from utils.functions import load_photo


class News(Resource):
    """
    Модуль работы с новостями
    """

    def __init__(self, db_worker: DBWorker, **kwargs) -> None:
        self.db_worker = db_worker

    def get(self) -> Response:
        """
        Выдаёт новость по ИД
        GET /api/news?id=
        {
            title
            content
            photo
            date
        }
        """
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            int(args['id'])
        except (TypeError, ValueError): # проверка типа
            message = 'Получен некорректный тип. ИД новости (id) должен быть int.'
            return jsonify({'status': 'warning', 'message': message})
        query = f"""
            SELECT
                portal.t_employee_base.full_name author,
                portal.t_news.news_text "content",
                portal.t_news.insert_date "date",
                portal.t_news.news_title "title"
            FROM portal.t_news
                LEFT JOIN portal.t_employee_base
                    ON portal.t_news.creator_id = portal.t_employee_base.employee_id
            WHERE portal.t_news.news_id = {args['id']}
        """
        try:
            result = self.db_worker.select_with_columns(query)[0]
            result['photo'] = load_photo('news_photo', str(args['id']))
        except IndexError:
            result = {'status': 'warning', 'message': f"Новость с id={args['id']} не найдена."}
        return jsonify(result)

    def post(self) -> Response:
        """
        Выдаёт последние новости
        POST /api/news
        {
            title
            content
            photo
            creator_id (будет после добавления авторизации)
        }
        """
        content = request.form.get('content')
        title = request.form.get('title')
        file_format = request.files['photo'].filename.split('.')[-1]
        try:
            str(content)
            str(title)
            assert file_format in ('jpg', 'png')
        except (TypeError, ValueError, AssertionError): # проверка типа
            message = 'Получен некорректный тип. Текст новости должен быть str, photo (файл) должен быть в формате jpg.'
            return jsonify({'status': 'warning', 'message': message})
        # записать в базу
        query = f"""
            INSERT INTO portal.t_news
                (news_text, creator_id, insert_date, update_date, status, news_title)
            VALUES ('{content}', 1, now(), now(), 1, '{title}')
            RETURNING news_id;
        """
        news_id = self.db_worker.exec_returning(query)[0]
        if not news_id:
            return jsonify({'status': 'alert', 'message': 'Ошибка записи в БД. Обратитесь к администратору'})
        # сохранить фотку
        photo_path = os.path.join('media', 'news_photo', f'{news_id}.{file_format}')
        request.files['photo'].save(photo_path)
        return jsonify(success=True)

    def put(self) -> Response:
        """
        Редактирование новости
        PUT /api/news?news_id=
        {
            title
            content
            photo
            date
            creator_id (будет после добавления авторизации)
        }
        """
        parser = reqparse.RequestParser()
        parser.add_argument('news_id')
        args = parser.parse_args()
        news_id = args['news_id']
        content = request.form.get('content')
        title = request.form.get('title')
        date = request.form.get('date')
        file_format = request.files['photo'].filename.split('.')[-1]
        try:
            int(news_id)
            str(content)
            str(title)
            date = datetime.strptime(date, '%d.%m.%Y %H:%M:%S')
            assert file_format in ('jpg', 'png')
        except (TypeError, ValueError, AssertionError): # проверка типа
            message = 'Получен некорректный тип. News_id должен быть int, content и title должны быть str, date должен быть str в формате "дд.мм.гггг ЧЧ:ММ:СС", photo должно быть в формате jpg.'
            return jsonify({'status': 'warning', 'message': message})
        query = f"""
            BEGIN;
                DELETE FROM portal.t_news
                    WHERE news_id = {news_id};
                INSERT INTO portal.t_news
                    (news_id, news_text, creator_id, insert_date, update_date, status, news_title)
                VALUES ({news_id}, '{content}', 1, '{date.strftime('%Y-%m-%d %H:%M:%S')}', now(), 1, '{title}');
            COMMIT;
        """
        done = self.db_worker.exec_command(query)
        if not done:
            return jsonify({'status': 'alert', 'message': 'Ошибка записи в БД. Обратитесь к администратору'})
        # сохранить фотку
        photo_path = os.path.join('media', 'news_photo', f'{news_id}.{file_format}')
        request.files['photo'].save(photo_path)
        return jsonify({'status': 'success', 'message': 'Новость изменена.'})

    def delete(self) -> Response:
        """
        Удаление новости
        DELETE /api/news?news_id=
        """
        parser = reqparse.RequestParser()
        parser.add_argument('news_id')
        args = parser.parse_args()
        try:
            int(args['news_id'])
        except (TypeError, ValueError, AssertionError): # проверка типа
            message = 'Получен некорректный тип. News_id должен быть int.'
            return jsonify({'status': 'warning', 'message': message})
        query = f"""
            DELETE FROM portal.t_news
                WHERE news_id = {args['news_id']};
        """
        done = self.db_worker.exec_command(query)
        if not done:
            return jsonify({'status': 'alert', 'message': 'Ошибка записи в БД. Обратитесь к администратору'})
        return jsonify({'status': 'success', 'message': 'Новость удалена.'})