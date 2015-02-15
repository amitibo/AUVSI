import sqlite3
from  datetime import datetime
import os


class DataBase(object):
    
    def __init__(
            self,
            base_path='~/db',
            images_db='images.db',
            images_table='image_table'
    ):

        #
        # Check if databases exists, if not create them
        #
        self.base_path = os.path.abspath(os.path.expanduser(base_path))
        self.images_db = os.path.join(self.base_path, images_db)
        self.images_table = images_table

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        self._cmd(
            cmd='create table if not exists {table_name} (id integer primary key, image_path text, [timestamp] timestamp)'.format(table_name=self.images_table)
        )
    
    def _cmd(self, cmd, params=()):
        
        print cmd
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
        self._cmd(cmd, (img_path, datetime.now()))

    def getNewImgs(self, timestamp):
        
        if timestamp is None:
            timestamp = datetime(year=1970, month=1, day=1)

        cmd = "SELECT * FROM {table_name} WHERE {table_name}.timestamp > '{timestamp}'".format(
            table_name=self.images_table,
            timestamp=timestamp
        )

        return self._cmd(cmd)
