from twisted.internet import reactor, task
from twisted.web.resource import Resource, NoResource
from twisted.web.server import Site

__all__ = (
    'start_server'
)


class CameraResource(Resource):
    def render_GET(self, request):
        
        #
        # Get the type of camera command
        #
        cmd = request.uri[1:].split('=')[1]
        if cmd == 'on':
            print 'on'
            return "<html><body>On!</body></html>"
            #self.camera_loop = task.LoopingCall(take_image)
            #self.camera_loop.start(1.0)

        elif cmd == 'off':
            print 'off'
            return "<html><body>Off!</body></html>"
            #self.camera_loop.stop()
        
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
