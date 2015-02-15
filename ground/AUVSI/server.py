from twisted.internet import reactor, protocol, task
from twisted.web.client import getPage
from twisted.enterprise import adbapi
from datetime import datetime
import os


def printPage(result):
    print result


def printError(failure):
    print failure


class CameraClient(protocol.Protocol):
    
    def connectionMade(self):
        self.factory.on_connection(self.transport)

    def connectionLost(self, reason):
        self.factory.on_disconnection(self.transport)

    def dataReceived(self, data):
        self.factory.app.print_message(data)

    
class ServerFactory(protocol.ReconnectingClientFactory):
    protocol = CameraClient
    images_task = None
    
    #
    # Parameters if reconnection.
    #
    maxDelay = 1
    initialDelay = 0.1
    
    #
    # Data base handling.
    #
    dbpool = None
    
    def __init__(
        self,
        app,
        database_path='~/auvsi_db',
        images_db='images.db',
        images_table='images_table'
        ):
        
        self.app = app

        #
        # Initialize database stuff
        #
        self.database_path = os.path.abspath(os.path.expanduser(database_path))
        self.images_db = os.path.join(self.database_path, images_db)
        self.images_table = images_table
    
        if not os.path.exists(self.database_path):
            os.makedirs(self.database_path)
    
        self.dbpool = adbapi.ConnectionPool("sqlite3", self.images_db)        

        self._db_cmd(
            cmd='create table if not exists {table_name} (id integer primary key, image_path text, [timestamp] timestamp)'.format(table_name=self.images_table)
        )

    def _db_cmd(self, cmd, params=()):
        print cmd
        return self.dbpool.runQuery(cmd, params)
    
    def on_connection(self, conn):
        self.app.on_connection(conn)

        #
        # Add task for getting new images.
        #
        self.images_task = task.LoopingCall(self.updateImagesDB)
        self.images_task.start(1)
        
    def on_disconnection(self, conn):
        self.app.on_disconnection(conn)
        
        if self.images_task is not None:
            self.images_task.stop()
            self.images_task = None
        
    def clientConnectionLost(self, conn, reason):
        self.app.print_message("connection lost")
        self.retry(conn)

    def clientConnectionFailed(self, conn, reason):
        self.app.print_message("connection failed")
        self.retry(conn)

    def _downloadNewImages(self, entries_list):
        
        for entry in entries_list:
            print entry
    
    def _lastTimeStamp(self, timestamp):
        
        if timestamp == []:
            timestamp = ''
    
        d = access('new_imgs='+timestamp, self._downloadNewImages)
    
    def updateImagesDB(self):

        #
        # Get last entry
        #
        cmd = 'SELECT timestamp FROM {table_name} WHERE ID = (SELECT MAX(ID) FROM {table_name})'.format(table_name=self.images_table)
        d = self._db_cmd(cmd)
        d.addCallback(self._lastTimeStamp)
        

def connect(app, server):
    reactor.connectTCP(
        server['ip'],
        int(server['port']),
        ServerFactory(app)
    )
    
    global _server_address
    _server_address = server

def access(page, callback=printPage):
    d = getPage(
        'http://{ip}:{port}/{page}'.format(ip=_server_address['ip'], port=_server['port'], page=page)
    )
    d.addCallbacks(callback, printError)
    return d