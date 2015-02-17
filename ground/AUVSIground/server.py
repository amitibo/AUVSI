from twisted.internet import reactor, protocol, task, threads
from twisted.web.client import getPage
from twisted.enterprise import adbapi
import global_settings as gs
from datetime import datetime
import urllib
import json
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
        app
        ):
        
        self.app = app

        #
        # Initialize database stuff
        #
        self.database_path = gs.DB_FOLDER
        self.images_db = gs.DB_PATH
        self.images_table = gs.IMAGES_TABLE
    
        if not os.path.exists(self.database_path):
            os.makedirs(self.database_path)
        if not os.path.exists(gs.IMAGES_FOLDER):
            os.makedirs(gs.IMAGES_FOLDER)
    
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
        
    def _dbNewImg(self, data):
        
        img_path, new_imgs = data
        
        new_img = new_imgs.pop(0)
        cmd = "INSERT INTO {table_name}(image_path, timestamp) values (?, ?)".format(table_name=self.images_table)
        d = self._db_cmd(cmd, (img_path, new_img['timestamp']))
        
        return new_imgs
    
    def _downloadNewImg(self, new_imgs):
        
        new_img = new_imgs[0]
        img_url = 'http://{ip}:{port}/images/{img}'.format(ip=_server_address['ip'], port=_server_address['port'], img=new_img['name'])
        img_path = os.path.join(gs.IMAGES_FOLDER, new_img['name'])
        
        print 'Downloading:', img_url, 'to', img_path
        
        urllib.urlretrieve(img_url, img_path)
        
        return img_path, new_imgs
    
    def _loopNewImgs(self, new_imgs):
        if len(new_imgs) == 0:
            self.images_task.start(1)
            return
        print len(new_imgs), 'images more to go.'
        d = threads.deferToThread(self._downloadNewImg, new_imgs)
        d.addCallback(self._dbNewImg)
        d.addCallback(self._loopNewImgs)        
    
    def _setupNewImagesLoop(self, entries_list):
        
        entries_list = json.loads(entries_list)
        
        if len(entries_list) == 0:
            return
        
        #
        # Stop checking for new images till all images downloaded.
        #
        self.images_task.stop()
        
        new_imgs = [{'name': os.path.split(entry[1])[1], 'timestamp': entry[2]} for entry in entries_list]
        print 'Setting up:', len(new_imgs), 'new images'
        self._loopNewImgs(new_imgs)
        
    def _lastTimeStamp(self, timestamp):
        
        if timestamp == []:
            timestamp = ''
        else:
            timestamp=timestamp[0][0].replace(' ', 'T')
            
        d = access('new_imgs='+timestamp, self._setupNewImagesLoop)
    
    def updateImagesDB(self):

        #
        # Get last entry
        #
        cmd = 'SELECT timestamp FROM {table_name} WHERE ID = (SELECT MAX(ID) FROM {table_name})'.format(table_name=self.images_table)
        d = self._db_cmd(cmd)
        d.addCallback(self._lastTimeStamp)
        

def setserver(ip, port):
    global _server_address
    _server_address = {'ip': ip, 'port': port}

_server = None

def connect(app):
    global _server
    
    if _server is not None:
        _server.stopTrying()
        
    _server = ServerFactory(app)
    reactor.connectTCP(
        _server_address['ip'],
        _server_address['port'],
        _server
    )
    


def access(page, callback=printPage):
    url = 'http://{ip}:{port}/{page}'.format(ip=_server_address['ip'], port=_server_address['port'], page=page)
    print 'Accessing url:', url
    d = getPage(url)
    d.addCallbacks(callback, printError)
    return d