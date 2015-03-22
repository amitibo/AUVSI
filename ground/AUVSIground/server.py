from twisted.internet import reactor, protocol, task, threads
from twisted.web.client import getPage, downloadPage
from twisted.enterprise import adbapi
from twisted.python import log
import global_settings as gs
from datetime import datetime
import urllib
import json
import cv2
import os


def logReply(result):
    log.msg(result)


def logError(failure):
    log.msg(failure)


class RemoteServer(protocol.Protocol):
    """Protocol for communicating with the remote server on the onboard computer"""
    
    def connectionMade(self):
        self.factory.on_connection(self.transport)

    def connectionLost(self, reason):
        self.factory.on_disconnection(self.transport)

    def dataReceived(self, data):
        self.factory.app.log_message(data)

    
class ServerFactory(protocol.ReconnectingClientFactory):
    protocol = RemoteServer
    images_task = None
    
    #
    # Reconnection parameters.
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

        #
        # Create the images_table. This is done without the twisted
        # ConnectionPool as the reactor is not yet started.
        #
        import sqlite3
        conn = sqlite3.connect(self.images_db)
        cursor = conn.cursor()
        cmd = 'create table if not exists {table_name} (id integer primary key, image_path text, image_tn_path text, [timestamp] timestamp)'.format(table_name=self.images_table)
        log.msg('Initiating database: {cmd}'.format(cmd=cmd))
        cursor.execute(cmd)
        conn.commit()
        conn.close()
        log.msg('Database initiated')
        
        self.dbpool = adbapi.ConnectionPool("sqlite3", self.images_db)        


    def _db_cmd(self, cmd, params=()):
        log.msg('Creating deferred sqlite3 cmd: {cmd}, {params}'.format(cmd=cmd, params=params))
        return self.dbpool.runQuery(cmd, params)
    
    def on_connection(self, conn):
        """Handle connection to remote server."""
        
        #
        # Notify the GUI application.
        #
        self.app.on_connection(conn)

        #
        # Add deffered task for getting new images.
        #
        self.images_task = task.deferLater(reactor, 1, self.updateImagesDB)
        
    def on_disconnection(self, conn):
        """Handle disconnection to remote server."""
    
        #
        # Notify the GUI application.
        #
        self.app.on_disconnection(conn)
        
        #
        # Stop the task of getting new images.
        #
        if self.images_task is not None:
            self.images_task.cancel()
            self.images_task = None
        
    def _dbNewImg(self, data):
        """Store the newly downloaded image in the database"""
        
        new_img_paths, new_imgs = data
        
        #
        # Add new image to list in gui
        #
        self.app._populateImagesList([new_img_paths])

        #
        # Store the new image in the data base and continue downloading the new images.
        #
        new_img = new_imgs.pop(0)
        cmd = "INSERT INTO {table_name}(image_path, image_tn_path, timestamp) values (?, ?, ?)".format(table_name=self.images_table)
        d = self._db_cmd(cmd, (new_img_paths[0], new_img_paths[1], new_img['timestamp']))
        d.addCallback(self._loopNewImgs)        
        
        #
        # Retrun the list of remaining images.
        #
        return new_imgs
    
    def _downloadNewImg(self, new_imgs):
        """Download a new image from the remote server. This function is run on a separate thread."""
        
        #
        # Set paths
        #
        new_img = new_imgs[0]['name']
        img_url = 'http://{ip}:{port}/images/{img}'.format(ip=_server_address['ip'], port=_server_address['port'], img=new_img)
        img_path = os.path.join(gs.IMAGES_FOLDER, new_img)
        new_img_tn = '{}_tn{}'.format(*os.path.splitext(new_img))
        img_tn_path = os.path.join(gs.IMAGES_FOLDER, new_img_tn)

        #
        # Download image
        #
        log.msg('Downloading image from url {img_url} to local path: {local_path}'.format(img_url=img_url, local_path=img_path))
        urllib.urlretrieve(img_url, img_path)
        log.msg('Finished Downloading image from url {img_url}'.format(img_url=img_url))
        
        #
        # Resize a thumbnail.
        #
        img = cv2.imread(img_path)
        r = 100.0 / img.shape[1]
        dim = (100, int(img.shape[0] * r))
        img_tn = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        cv2.imwrite(img_tn_path, img_tn)
        
        return (img_path, img_tn_path), new_imgs
    
    def _loopNewImgs(self, new_imgs):
        """Loop on all new images. Download and store in database each image."""
        
        log.msg('Following images left to download: {new_imgs}'.format(new_imgs=new_imgs))
        
        if len(new_imgs) == 0:
            #
            # Finished processing all new images.
            #
            self.images_task = task.deferLater(reactor, 1, self.updateImagesDB)
            return
        
        #
        # Download new images on a separate thread and store them in the database.
        #
        d = threads.deferToThread(self._downloadNewImg, new_imgs)
        d.addCallback(self._dbNewImg)
    
    def _setupNewImagesLoop(self, entries_list):
        """Handle the reply of the remote server with the list of new images  (newer timestamp)."""
        
        entries_list = json.loads(entries_list)
        
        if len(entries_list) == 0:
            #
            # No new images.
            #
            self.images_task = task.deferLater(reactor, 1, self.updateImagesDB)
            return
        
        new_imgs = [{'name': os.path.split(entry[1])[1], 'timestamp': entry[2]} for entry in entries_list]
        self._loopNewImgs(new_imgs)
        
    def _sendLastTimeStamp(self, timestamp):
        """Ask the remote server for images with timestamp later then timestamp of the last entry in the image database."""
        
        if timestamp == []:
            #
            # The image database is empty
            #
            timestamp = ''
        else:
            timestamp=timestamp[0][0].replace(' ', 'T')
        
        #
        # Send query to remote server.
        #
        d = access('new_imgs='+timestamp, callback=self._setupNewImagesLoop)
    
    def updateImagesDB(self):
        """Entry point for the image synchronization task."""
        
        #
        # Get the time stamp of the last entry in the image database.
        #
        cmd = 'SELECT timestamp FROM {table_name} WHERE ID = (SELECT MAX(ID) FROM {table_name})'.format(table_name=self.images_table)
        d = self._db_cmd(cmd)
        d.addCallback(self._sendLastTimeStamp)
    
    def _filterImagesPath(self, db_reply):
        """"""
        images_list = [items[:2] for items in db_reply]
        return images_list
    
    def getImagesList(self, callback):
        """Get the list of images in the data base"""
        
        cmd = 'SELECT image_path, image_tn_path, timestamp FROM {table_name}'.format(table_name=self.images_table)
        d = self._db_cmd(cmd)
        d.addCallback(self._filterImagesPath)
        d.addCallback(callback)
        

def setserver(ip, port):
    """Set the server address"""
    
    global _server_address
    _server_address = {'ip': ip, 'port': port}


_server = None

def connect(app):
    """Start the twisted server."""
    
    global _server
    
    if _server is not None:
        _server.stopTrying()
        
    _server = ServerFactory(app)
    reactor.connectTCP(
        _server_address['ip'],
        _server_address['port'],
        _server
    )
    
    return _server


def access(page, args=None, callback=logReply):
    """Access a webpage."""
    
    url = 'http://{ip}:{port}/{page}'.format(ip=_server_address['ip'], port=_server_address['port'], page=page)
    if args is not None:
        url += '?{args_string}'.format(
            args_string='&'.join(['{k}={v}'.format(k=k, v=v) for k, v in args.items()])
        )
    d = getPage(url)
    d.addCallbacks(callback, logError)
    
    return d