from twisted.internet import reactor, threads
from twisted.web.resource import Resource, NoResource
from twisted.python import filepath
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from twisted.python.logfile import DailyLogFile

from camera import SimulationCamera, CanonCamera
import global_settings as gs
from database import DataBase
import platform
import json
import os


__all__ = (
    'start_server'
)


#
# Global objects
#
database = DataBase()


class CameraResource(Resource):
    """Handle camera related communication."""
    
    def render_GET(self, request):
        """"""
        #
        # Get the type of camera command
        #
        cmd = request.prepath[0]
        args = request.args
        
        if cmd == 'camera_on':
            camera.startShooting()

            return "<html><body>On!</body></html>"

        elif cmd == 'camera_off':
            camera.stopShooting()

            return "<html><body>Off!</body></html>"

        elif cmd == 'camera_set':
            for key, item in args.items():
                if getattr(camera, key) == None:
                    log.msg('Ignoring unkown camera settings: {key}, {item}'.format(key=key, item=item))
                    continue
                
                setattr(camera, key, int(item[0]))
        else:
            return NoResource()


class ImagesResource(Resource):
    """Handle image related communication."""

    def render_GET(self, request):
        
        #
        # Get the timestamp
        #
        splits = request.uri[1:].split('=')
        if len(splits) > 1:
            timestamp = splits[1]
        else:
            timestamp = None

        new_imgs = database.getNewImgs(timestamp)

        return json.dumps(new_imgs)


class HTTPserverMain(Resource):
    """HTTPserverMain handles the communication with the ground station."""
    
    def getChild(self, name, request):
        if name == '':
            return self
        if name.startswith('camera'):
            return CameraResource()
        elif name.startswith('new_imgs'):
            return ImagesResource()
        else:
            return NoResource()

    def render_GET(self, request):
        return "<html><body>Welcome to the AUSVI drone!</body></html>"


class FileSystemWatcher(object):
    """
    Watch for newly created files in a folder.

    This is used for notifying when an imaged was captured by the camera.
    
    Parameters
    ----------
    path_to_watch : string
        Name of path to watch.
    """
    
    def __init__(self, path_to_watch):
        self.path_to_watch = path_to_watch

    def _watchThread(self):
        from watch_directory import watch_path
        
        for file_type, filename, action in watch_path(self.path_to_watch):
            if action == "Created":
                self.OnChange(filename)
    
    def _inotifyCB(self, watch, path, mask):
        self.OnChange(path.path)
        
    def Start(self):
        """Start watching the path."""
        
        if platform.system() == 'Linux':
            #
            # On linux it is possible to use the inotify api.
            #
            from twisted.internet import inotify
            
            notifier = inotify.INotify()
            notifier.startReading()
            notifier.watch(
                filepath.FilePath(self.path_to_watch),
                mask=inotify.IN_CREATE,
                callbacks=[self._inotifyCB]
            )
    
        else:
            #
            # On windows we use a method from:
            # http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
            #
            d = threads.deferToThread(self._watchThread)
            
    def OnChange(self, path):
        database.storeImg(path)


def start_server(camera_type ,port=8000):
    """
    Start the airborne server.
    
    Parameters
    ----------
    camera_type: string
        Camera type. Options: [canon (default), simlulation].
    port: int, optional(=8000)
        Port used by server.
    """
    
    #
    # Setup logging.
    #
    if not os.path.exists(gs.AUVSI_BASE_FOLDER):
        os.makedirs(gs.AUVSI_BASE_FOLDER)
        

    f = DailyLogFile('server.log', gs.AUVSI_BASE_FOLDER)
    log.startLogging(f)

    #
    # Create the camera object.
    #
    global camera
    if camera_type.lower() == 'canon':
        camera = CanonCamera()
    elif camera_type.lower() == 'simulation':
        camera = SimulationCamera()
    else:
        raise NotImplementedError('Camera type {camera}, not supported.'.format(camera=camera_type))
    
    #
    # add a watcher on the images folder
    #
    fs = FileSystemWatcher(gs.IMAGES_FOLDER)
    fs.Start()

    #
    # Config the server
    #
    root = HTTPserverMain()
    root.putChild("images", File(camera.base_path.encode('ascii', 'ignore')))
    factory = Site(root)

    #
    # Startup the reactor.
    #
    reactor.listenTCP(port, factory)
    reactor.run()
