from twisted.internet import reactor, task
from twisted.web.resource import Resource, NoResource
from twisted.web.server import Site
from camera import camera_mockup

__all__ = (
    'start_server'
)


camera = camera_mockup()


class CameraResource(Resource):
    camera_loop = None

    def render_GET(self, request):
        
        #
        # Get the type of camera command
        #
        cmd = request.uri[1:].split('=')[1]
        if cmd == 'on':
            CameraResource.camera_loop = task.LoopingCall(camera.shoot)
            CameraResource.camera_loop.start(1.0)

            return "<html><body>On!</body></html>"

        elif cmd == 'off':
            if CameraResource.camera_loop is not None:
                CameraResource.camera_loop.stop()
                CameraResource.camera_loop = None

            return "<html><body>Off!</body></html>"
        
        else:
            return NoResource()


       
class MainLoop(Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        if name.startswith('camera'):
            return CameraResource()

        else:
            return NoResource()

    def render_GET(self, request):
        return "<html><body>Welcome to the AUSVI drone!</body></html>"



def start_server(port=8000):
    root = MainLoop()
    factory = Site(root)

    reactor.listenTCP(port, factory)
    reactor.run()
