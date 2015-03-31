from twisted.internet import reactor, threads
from twisted.web.resource import Resource, NoResource
from twisted.python import filepath
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from twisted.python.logfile import DailyLogFile

from camera import SimulationCamera, CanonCamera
import global_settings as gs
import database as DB
import images as IM
import PixHawk as PH
import platform
import json
import os


__all__ = (
    'start_server'
)


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
            params_dict = {key:int(val[0]) for key, val in args.items()}
            camera.setParams(**params_dict)

        else:
            return NoResource()


class CVResource(Resource):
    """Handle image processing related communication."""
    
    def render_GET(self, request):
        """"""
        #
        # Get the type of command
        #
        cmd = request.prepath[0]
        args = request.args
        
        if cmd == 'cv_set':
            for key, item in args.items():
                #
                # TODO: handle cv settings.
                #
                pass
            
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

        new_imgs = DB.getNewImgs(timestamp)

        log.msg('Datebase got the following new images:\n{new_imgs}'.format(new_imgs=new_imgs))
        
        return json.dumps(new_imgs)


class CropResource(Resource):
    """Handle crop related communication."""

    def render_GET(self, request):
        
        args = request.args

        #
        # Get the timestamp
        #
        splits = request.uri[1:].split('=')
        if len(splits) > 1:
            timestamp = splits[1]
        else:
            timestamp = None

        new_imgs = DB.getNewImgs(timestamp)

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
        elif name.startswith('crop'):
            return CropResource()
        else:
            return NoResource()

    def render_GET(self, request):
        return "<html><body>Welcome to the AUSVI drone!</body></html>"


class FileSystemWatcher(object):
    """
    Watch for newly created files in a folder.

    This is used for notifying when an image was captured by the camera.
    
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
        log.msg('Identified new image {img}'.format(img=path))
        IM.handleNewImage(path)


def start_server(camera_type, simulate_pixhawk, port=8000):
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
    # Create the auvsi data folder.
    #
    if not os.path.exists(gs.AUVSI_BASE_FOLDER):
        os.makedirs(gs.AUVSI_BASE_FOLDER)
        
    #
    # Setup logging.
    #
    f = DailyLogFile('server.log', gs.AUVSI_BASE_FOLDER)
    log.startLogging(f)

    #
    # Initialize the data base.
    #
    DB.initDB()
    
    #
    # Initialize the imageprocessing module.
    #
    IM.initIM()
    
    #
    # Initialize the pixhawk module.
    #
    if not simulate_pixhawk:
        PH.initPixHawk()
    else:
        PH.initPixHawkSimulation()
    
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
    root.putChild("images", File(gs.RESIZED_IMAGES_FOLDER))
    factory = Site(root)

    #
    # Startup the reactor.
    #
    reactor.listenTCP(port, factory)
    reactor.run()
