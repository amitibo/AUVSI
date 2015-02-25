from twisted.internet import reactor, threads
from twisted.web.resource import Resource, NoResource
from twisted.python import filepath
from twisted.web.server import Site
from twisted.web.static import File
from camera import SimulationCamera, CanonCamera
import global_settings as gs
from database import DataBase
import platform
import json


__all__ = (
    'start_server'
)


#
# Global objects
#
database = DataBase()


#
# server resources
#
class CameraResource(Resource):

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
                    print 'Ignoring unkown camera settings:', key, item
                    continue
                
                setattr(camera, key, int(item[0]))
        else:
            return NoResource()


#
# server resources
#
class ImagesResource(Resource):

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


#
# MainLoop of the server
#
class MainLoop(Resource):

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
        print path, 'changed'
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
    # Create the camera object.
    #
    global camera
    if camera_type.lower() == 'canon':
        camera = CanonCamera()
    elif camera_type.lower() == 'simulation':
        camera = SimulationCamera()
    else:
        raise NotImplementedError('Camera type {camera}, not supported.'.format(camera=camera_type))
    
    root = MainLoop()
    root.putChild("images", File(camera.base_path))
    factory = Site(root)

    #
    # add a watcher on the images folder
    #
    fs = FileSystemWatcher(gs.IMAGES_FOLDER)
    fs.Start()

    reactor.listenTCP(port, factory)
    reactor.run()
