# coding=utf-8

import logging
import os
import secrets
import flask
import werkzeug
import flask_caching
import pymysql


cache_info = {
    'CACHE_TYPE': os.getenv('CACHE_TYPE', 'simple'),
    'CACHE_REDIS_HOST': os.getenv('CACHE_REDIS_HOST', 'localhost'),
    'CACHE_REDIS_PORT': int(os.getenv('CACHE_REDIS_PORT', '6379')),
    'CACHE_REDIS_PASSWORD': os.getenv('CACHE_REDIS_PASSWORD', 'password')
}

db_info = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'app'),
    'password': os.getenv('DB_PASS', 'password'),
    'db': os.getenv('DB_NAME', 'pastebin')
}


app = flask.Flask(__name__)
cache = flask_caching.Cache(app, config=cache_info)


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
def get_post(post_id, **kwargs):
    db_conn: pymysql.Connection = kwargs['db']
    with db_conn.cursor() as cur:
        sql = 'select * from posts where id = %s'
        cur.execute(sql, (post_id,))
        ret = cur.fetchone()
        if not ret:
            raise werkzeug.exceptions.NotFound(f'Post {post_id} not found')
        return flask.jsonify(**ret)


@inject_db
def create_post(title, content, **kwargs):
    db_conn: pymysql.Connection = kwargs['db']
    id_ = secrets.token_hex(16)
    with db_conn.cursor() as cur:
        sql = 'insert into posts(id, title, content) values (%s, %s, %s)'
        cur.execute(sql, (id_, title, content))
        return {'id': id_}


@inject_db
def update_post(id_, title, content, **kwargs):
    db_conn: pymysql.Connection = kwargs['db']
    with db_conn.cursor() as cur:
        sql = 'update posts set title = %s, content = %s where id = %s'
        cur.execute(sql, (title, content, id_))
        return {'id': id_}


@app.route('/posts/<string:post_id>', methods=['GET', 'PUT'])
def post(post_id):
    method = flask.request.method
    if method == 'GET':
        return get_post(post_id)
    else:
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
    return create_post(**data)
