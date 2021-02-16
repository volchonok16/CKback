import flask
import logging

# быстрая NoSQL для работы с сессиями
from redis import Redis
# настройки сервера
from flask_cors import CORS
from flask_restful import Api
from flask import Flask, request
from flask.json import JSONEncoder
from flask.wrappers import Response
# профилирование
from werkzeug.middleware.profiler import ProfilerMiddleware
# объект защиты системы
from api.sentry import Sentry
# работа с датой и временем
from datetime import date, datetime
# работа с базой
from dbworker import DBWorker
# ресурсы
from api.auth.main import Auth
from api.auth.code import Code
from api.auth.register import Register
from api.user.main import User
from api.user.me import Me
from api.users.short_list import UsersShortList
from api.users.list import UsersList
from api.internship import main, take, lessons, completed, active, recent, by_month
from api.internship.list_students import StudentsShortList
from api.internship.students import StudentInternshipStatus
from api.internship.homework import Homework
from api.files.course_contents import FilesCourseContents
from api.tests import tests_main
from api.certificates.main import CertificatesMain
from api.certificates.my import CertificatesMy
from api.certificates.list import CertificatesList
from api.news.main import News
from api.news.list import NewsList
from api.skills.list import SkillsList
from api.ticket import create_internship

from api.ticket.enroll import SighUpInternship


class JE(JSONEncoder):
    """
    Необходим для фикса неправильного формата даты
    https://stackoverflow.com/questions/43663552/keep-a-datetime-date-in-yyyy-mm-dd-format-when-using-flasks-jsonify
    """
    def default(self, o):
        if isinstance(o, date):
            return o.strftime('%d.%m.%Y %H:%M:%S')
        return super().default(o)


class FlaskJE(Flask):
    """
    Привязываем кастомный энкодер json'ов к аппке Flask
    """
    json_encoder = JE


def run_server(config: dict, db_worker: DBWorker, redis_client: Redis) -> None:
    logging.debug('Настраиваем и запускаем сервер.')
    app = FlaskJE(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSON_AS_ASCII'] = False
    api = Api(app)
    cors = CORS(app, expose_headers=["x-suggested-filename"], resources={r"/api/*": {"origins": '*'}}, supports_credentials=True)
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [15], sort_by=('tottime', 'calls'))

    @app.before_request
    def before() -> None:
        # if request.endpoint not in ('auth', 'code') and request.method != 'OPTIONS': # пропускаем только работу с аутентификацией
        #     Sentry(request, redis_client)
        pass

    @app.after_request
    def after(response: Response) -> Response:
        return response

    rck = {'db_worker': db_worker, 'redis_client': redis_client} # rck - resource_class_kwargs

    # Аутентификация
    api.add_resource(Auth, '/api/auth', resource_class_kwargs=rck)
    api.add_resource(Code, '/api/auth/code', resource_class_kwargs=rck)
    api.add_resource(Register, '/api/auth/register', resource_class_kwargs=rck)
    # Работа с файлами
    api.add_resource(FilesCourseContents, '/api/files/course_contents', resource_class_kwargs=rck)
    # Пользователь
    api.add_resource(User, '/api/user', resource_class_kwargs=rck)
    api.add_resource(Me, '/api/user/me', resource_class_kwargs=rck)
    # Стажировки
    api.add_resource(main.Internship, '/api/internship', resource_class_kwargs=rck)
    api.add_resource(take.InternshipTake, '/api/internship/take', resource_class_kwargs=rck)
    api.add_resource(lessons.InternshipLessons, '/api/internship/lessons', resource_class_kwargs=rck)
    api.add_resource(active.InternshipActive, '/api/internship/active', resource_class_kwargs=rck)
    api.add_resource(completed.InternshipCompleted, '/api/internship/completed', resource_class_kwargs=rck)
    api.add_resource(recent.InternshipRecent, '/api/internship/recent', resource_class_kwargs=rck)
    api.add_resource(by_month.InternshipByMonth, '/api/internship/by_month', resource_class_kwargs=rck)
    api.add_resource(StudentsShortList, '/api/internship/list_students', resource_class_kwargs=rck)
    api.add_resource(StudentInternshipStatus, '/api/internship/students', resource_class_kwargs=rck)
    api.add_resource(Homework, '/api/internship/homework', resource_class_kwargs=rck)
    # Тесты
    api.add_resource(tests_main.TestsMain, '/api/tests', resource_class_kwargs=rck)     
    # Сертификаты
    api.add_resource(CertificatesMy, '/api/certificates/my', resource_class_kwargs=rck)
    api.add_resource(CertificatesMain, '/api/certificates', resource_class_kwargs=rck)
    api.add_resource(CertificatesList, '/api/certificates/list', resource_class_kwargs=rck)
    # Новости
    api.add_resource(News, '/api/news', resource_class_kwargs=rck)
    api.add_resource(NewsList, '/api/news/list', resource_class_kwargs=rck)
    # Пользователи
    api.add_resource(UsersShortList, '/api/users/short_list', resource_class_kwargs=rck)
    api.add_resource(UsersList, '/api/users/list', resource_class_kwargs=rck)
    # Навыки
    api.add_resource(SkillsList, '/api/skills/list', resource_class_kwargs=rck)
    # Тикеты
    api.add_resource(create_internship.TicketCreateInternship, '/api/ticket/create_internship', resource_class_kwargs=rck)
    api.add_resource(SighUpInternship, '/api/ticket/enroll', resource_class_kwargs=rck)

    app.run(**config['server_backend'])