# coding=utf-8

import logging
import os
import secrets
import flask
import werkzeug
import pymysql
import celery


schedule = celery.Celery(__name__,
                         broker=os.getenv('CELERY_BROKER_URL', 'pyamqp://'),
                         backend=os.getenv('CELERY_RESULT_BACKEND', 'rpc://'))

db_info = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'app'),
    'password': os.getenv('DB_PASS', 'password'),
    'db': os.getenv('DB_NAME', 'pastebin')
}


app = flask.Flask(__name__)


def inject_db(func):
    def decorator(*args, **kwargs):
        db_conn = pymysql.connect(
            **db_info,
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            kwargs['db'] = db_conn
            ret = func(*args, **kwargs)
            db_conn.commit()
        except pymysql.Error as err:
            logging.error(str(err))
            db_conn.rollback()
        else:
            return ret
        finally:
            db_conn.close()
    return decorator


@inject_db
def create_post(id_, title, content, **kwargs):
    db_conn: pymysql.Connection = kwargs['db']
    with db_conn.cursor() as cur:
        sql = 'insert into posts(id, title, content) values (%s, %s, %s)'
        cur.execute(sql, (id_, title, content))


@inject_db
def update_post(id_, title, content, **kwargs):
    db_conn: pymysql.Connection = kwargs['db']
    with db_conn.cursor() as cur:
        sql = 'update posts set title = %s, content = %s where id = %s'
        cur.execute(sql, (title, content, id_))
        return {'id': id_}


@schedule.task(bind=True)
def async_create_post(self, **kwargs):
    kwargs.update({'id_': self.request.id})
    create_post(**kwargs)


@app.route('/posts/<string:post_id>', methods=['PUT'])
def post(post_id):
    title = flask.request.json.get('title')
    content = flask.request.json.get('content')
    if None in (title, content):
        raise werkzeug.exceptions.BadRequest('title and content is required')
    update_post(post_id, title, content)
    return werkzeug.wrappers.Response(status=204)


@app.route('/posts', methods=['POST'])
def new_post():
    data = flask.request.json
    if 'title' not in data or 'content' not in data:
        raise werkzeug.exceptions.BadRequest('title and content is required')
    task = async_create_post.delay(**data)
    return {'id': task.id}
