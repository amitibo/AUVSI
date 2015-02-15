from twisted.internet import reactor, task
from twisted.web.resource import Resource, NoResource
from twisted.web.server import Site
from twisted.web.static import File
from camera import MockupCamera
from database import DataBase
import json


__all__ = (
    'start_server'
)


#
# Global objects
#
camera = MockupCamera()
database = DataBase()

#
# Callbacks
#
def shootCallBack(img_path):
    database.storeImg(img_path)


#
# server resources
#
class CameraResource(Resource):
    camera_loop = None

    def render_GET(self, request):
        
        #
        # Get the type of camera command
        #
        cmd = request.uri[1:].split('=')[1]
        if cmd == 'on':
            CameraResource.camera_loop = task.LoopingCall(camera.shoot, shootCallBack)
            CameraResource.camera_loop.start(1.0)

            return "<html><body>On!</body></html>"

        elif cmd == 'off':
            if CameraResource.camera_loop is not None:
                CameraResource.camera_loop.stop()
                CameraResource.camera_loop = None

            return "<html><body>Off!</body></html>"
        
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



def start_server(port=8000):
    root = MainLoop()
    root.putChild("images", File(camera.base_path))
    factory = Site(root)

    reactor.listenTCP(port, factory)
    reactor.run()
