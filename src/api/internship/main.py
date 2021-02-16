import os
import uuid
import json
import redis
import base64

from flask import jsonify
from flask_restful import Resource, reqparse, request
from flask.wrappers import Response

from dbworker import DBWorker

from utils.functions import strip_time

from datetime import datetime


class Internship(Resource):
    """
    Стажировка
    """

    def __init__(self, db_worker: DBWorker, redis_client: redis.Redis, **kwargs) -> None:
        self.db_worker = db_worker
        self.redis_client = redis_client

    def get(self) -> Response:
        """
        Информация о стажировке
        GET /api/internship?id=

        (Резултат большой смотри документацию на конфе)
        """

        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            int(args['id'])
        except (TypeError, ValueError): # проверка типа
            return jsonify({'status': 'warning', 'message': 'Получен некорректный тип, id должен быть int.'})

        query = f"""
                SELECT course_id as id, 
                    course_name as name,
                    (date_to - date_from) as duration,
                    description, 
                    target_audience_desc, 
                    lessons_json, 
                    is_inner, 
                    is_online, 
                    date_from, 
                    date_to
                FROM portal.t_courses_base
                WHERE course_id={args['id']};
                """

        result = self.db_worker.select_with_columns(query)

        result[0]['date_from'] = strip_time(result[0]['date_from'])
        result[0]['date_to'] = strip_time(result[0]['date_to'])
        lessons = json.loads(fr'''{result[0]['lessons_json']}'''.replace('\'', '\"'))

        for lesson in lessons:
            del lesson['lesson_id']
            del lesson['objectives']
            del lesson['homework']
            del lesson['test_url']
            del lesson['materials']

        result[0]['lectures_total'] = len(lessons)
        result[0]['program'] = lessons
        del result[0]['lessons_json']

        return jsonify(result[0])

    def post(self) -> Response:
        """
        Создание новой стажировки
        POST /api/internship
        {
            "ticket_id": 1,
            "comments": "Опционально", # при создании стажировки без заявки комментов менеджера нет
            "course_name": "Название стажировки",
            "is_inner": true/false,
            "is_online": true/false,
            "skills": ["Java", "Python", ...],
            "date_from": "10.03.2020",
            "date_to": "10.03.2020",
            "students": [42, 69, 420, ...],
            "mentors": [1337, ...],
            "description": "Что даст вам эта стажировка?",
            "target_audience_desc": "Для кого эта стажировка?"
        }
        """
        ticket_id = request.json.get('ticket_id')
        comments = request.json.get('comments')
        course_name = request.json.get('course_name')
        is_inner = request.json.get('is_inner')
        is_online = request.json.get('is_online')
        skills = request.json.get('skills')
        date_from = request.json.get('date_from')
        date_to = request.json.get('date_to')
        students = request.json.get('students')
        mentors = request.json.get('mentors')
        description = request.json.get('description')
        target_audience_desc = request.json.get('target_audience_desc')
        try:
            if not ticket_id is None:
                int(ticket_id)
            else:
                ticket_id = ''
            str(comments)
            str(course_name)
            assert isinstance(is_inner, bool)
            assert isinstance(is_online, bool)
            list(skills)
            datetime.strptime(date_from, '%m.%d.%Y')
            datetime.strptime(date_to, '%m.%d.%Y')
            list(students)
            list(mentors)
            str(description)
            str(target_audience_desc)
        except (TypeError, ValueError, AssertionError):  # проверка типа
            return jsonify({'status': 'warning', 'message': "Получен некорректный тип данных. Обратитесь к документации."})
        try:
            employee_id = self.redis_client.hget(request.headers['Authorization'], "employee_id").decode('utf-8')
        except (KeyError, AttributeError):
            return jsonify({'status': 'warning', 'message': 'В вашем запросе отсутствует header с сессией. Как вы здесь оказались?'})
        
        # формируем запрос на добавление менторов в t_course_mentors
        insert_mentors = "INSERT INTO portal.t_course_mentors (employee_id, course_id) VALUES"
        for mentor_id in mentors:
            insert_mentors += f"({mentor_id}, currval('portal.t_courses_course_id_seq')),"  

        # формируем запрос на добавление студентов в t_course_mentors
        insert_students = "INSERT INTO portal.t_course_student (employee_id, course_id) VALUES"
        for student_id in students:
            insert_students += f"({student_id}, currval('portal.t_courses_course_id_seq')),"

        # загружаем стажировку
        command = f"""
            BEGIN;
                INSERT INTO portal.t_courses_base
                    (course_name, skills, creator_id, "comments", topic, is_inner, description,
                    target_audience_desc, lessons_json, is_online, ticket_id, creation_date, date_from, date_to)
                VALUES
                    ('{course_name}', '{', '.join(skills)}', {employee_id}, '{comments}', '', {is_inner}, '{description}',
                     '{target_audience_desc}', '', {is_online}, {ticket_id}, now(), '{date_from}', '{date_to}');

                {insert_mentors[:-1]};

                {insert_students[:-1]};
            COMMIT;
        """
        done = self.db_worker.exec_command(command)
        if done:
            return jsonify({'status': 'success', 'message': "Создана новая стажировка."})
        else:
            return jsonify({'status': 'alert', 'message': "Ошибка записи в БД."})