from twisted.internet import reactor, inotify
from twisted.web.resource import Resource, NoResource
from twisted.python import filepath
from twisted.web.server import Site
from twisted.web.static import File
from camera import CanonCamera
import global_settings as gs
from database import DataBase
import json


__all__ = (
    'start_server'
)


#
# Global objects
#
camera = CanonCamera()
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
        cmd = request.uri[1:].split('=')[1]
        if cmd == 'on':
            camera.startShooting()

            return "<html><body>On!</body></html>"

        elif cmd == 'off':
            camera.stopShooting()

            return "<html><body>Off!</body></html>"

        elif cmd == 'set':
            print dir(request)
            
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
        self.path = path_to_watch

    def Start(self):
        notifier = inotify.INotify()
        notifier.startReading()
        notifier.watch(
            filepath.FilePath(self.path),
            callbacks=[self.OnChange]
        )

    def OnChange(self, watch, path, mask):
        print path, 'changed'
        database.storeImg(path.path)


def start_server(port=8000):
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
