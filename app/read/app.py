# coding=utf-8

import logging
import os
import flask
import werkzeug
import pymysql


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
def get_post(post_id, **kwargs):
    db_conn: pymysql.Connection = kwargs['db']
    with db_conn.cursor() as cur:
        sql = 'select * from posts where id = %s'
        cur.execute(sql, (post_id,))
        ret = cur.fetchone()
        if not ret:
            raise werkzeug.exceptions.NotFound(f'Post {post_id} not found')
        return flask.jsonify(**ret)


@app.route('/posts/<string:post_id>', methods=['GET'])
def get_post_api(post_id):
    return get_post(post_id)
