import sqlite3
from twisted.python import log
from  datetime import datetime
import global_settings as gs
import os


class DataBase(object):
    
    def __init__(self):

        #
        # Check if databases exists, if not create them
        #
        self.base_path = gs.DB_FOLDER
        self.images_db = gs.DB_PATH
        self.images_table = gs.IMAGES_TABLE

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        self._cmd(
            cmd='create table if not exists {table_name} (id integer primary key, image_path text, [timestamp] timestamp)'.format(table_name=self.images_table)
        )
    
    def _cmd(self, cmd, params=()):
        
        log.msg('Creating deferred sqlite3 cmd: {cmd}, {params}'.format(cmd=cmd, params=params))
        conn = sqlite3.connect(self.images_db)
        cursor = conn.cursor()
        cursor.execute(cmd, params)
        result = list(cursor)
        conn.commit()
        cursor.close()
        conn.close()

        return result

    def storeImg(self, img_path):
        
        cmd = "INSERT INTO {table_name}(image_path, timestamp) values (?, ?)".format(table_name=self.images_table)
        self._cmd(cmd, (img_path, datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))

    def getNewImgs(self, timestamp):
        
        if timestamp is None:
            timestamp = datetime(year=1970, month=1, day=1)

        cmd = "SELECT * FROM {table_name} WHERE {table_name}.timestamp > '{timestamp}'".format(
            table_name=self.images_table,
            timestamp=timestamp
        )

        return self._cmd(cmd)
