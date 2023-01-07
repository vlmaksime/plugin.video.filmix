import json
import os
import sqlite3

__all__ = ['FilmixCache']


class FilmixCache(object):

    def __init__(self, cache_dir):
        self._version = 2

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        db_path = os.path.join(cache_dir, 'cache{0}.db'.format(self._version))
        db_exist = os.path.exists(db_path)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = self._dict_factory

        if not db_exist:
            self.create_database()

    def __del__(self):
        self.conn.close()

    @staticmethod
    def _dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def create_database(self):

        c = self.conn.cursor()
        # posts
        c.execute('CREATE TABLE posts (post_id text, details text)')
        c.execute('CREATE UNIQUE INDEX posts_idx ON posts(post_id)')
        # translations
        c.execute('CREATE TABLE translations (post_id text, translation text)')
        c.execute('CREATE UNIQUE INDEX translations_idx ON translations(post_id)')

        self.conn.commit()

    def get_post_details(self, post_id):
        sql_params = {'post_id': post_id}

        c = self.conn.cursor()
        c.execute('SELECT details FROM posts WHERE post_id = :post_id LIMIT 1', sql_params)

        result = c.fetchone()
        if result is not None:
            return json.loads(result['details'])

    def set_post_details(self, post_id, details):

        sql_params = {'post_id': post_id, 'details': json.dumps(details)}

        c = self.conn.cursor()
        c.execute('INSERT OR REPLACE INTO posts (post_id, details) VALUES (:post_id, :details)', sql_params)

        self.conn.commit()

    def get_post_translation(self, post_id):
        sql_params = {'post_id': post_id}

        c = self.conn.cursor()
        c.execute('SELECT translation FROM translations WHERE post_id = :post_id LIMIT 1', sql_params)

        result = c.fetchone()
        if result is not None:
            return result['translation']

    def set_post_translation(self, post_id, translation):

        sql_params = {'post_id': post_id, 'translation': translation}

        c = self.conn.cursor()
        c.execute('INSERT OR REPLACE INTO translations (post_id, translation) VALUES (:post_id, :translation)',
                  sql_params)

        self.conn.commit()
