from twisted.internet import reactor, threads
from twisted.web.resource import Resource, NoResource
from twisted.python import filepath
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from twisted.python.logfile import DailyLogFile

from camera import SimulationCamera, CanonCamera
from datetime import datetime
import global_settings as gs
import database as DB
import images as IM
import PixHawk as PH
import platform
import Image
import json
import zmq
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPushConnection, ZmqPullConnection
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


def getFlightData(timestamp, K):
    
    #
    # Get the closest time stamp and save it with the image.
    #
    flight_data = PH.queryPHdata(timestamp)
    flight_data['K'] = K.tolist()
    flight_data['resized_K'] = True
    
    return flight_data
     

def handleNewImage(path):

    current_time = datetime.now()

    try:
        #
        # Check if the image is already renamed (which means that it is
        # a simulation camera)
        # NOTE:
        # The new image name is always based on the current time. But
        # in case its a simulation camera, the old image name is used
        # as timestamp for detecting corresponding flight_data.
        #
        img_name = os.path.split(path)[-1]
        img_time = datetime.strptime(img_name[:-4], gs.BASE_TIMESTAMP)
    except:
        img_time = current_time
    
    img_timestamp = img_time.strftime(gs.BASE_TIMESTAMP)
    current_timestamp = current_time.strftime(gs.BASE_TIMESTAMP)
    
    #
    # Handle the new image
    #
    resized_img_path, timestamp, K = IM.handleNewImage(path, current_timestamp)
    resized_img_name = os.path.split(resized_img_path)[-1]
    
    #
    # Get and save the flight data.
    #
    flight_data = getFlightData(img_timestamp, K)    
    flight_data_path = os.path.splitext(resized_img_path)[0]+'.json'
    with open(flight_data_path, 'wb') as f:
        json.dump(flight_data, f)
    log.msg('Saving flight data to path {path}'.format(path=os.path.split(flight_data_path)[-1]))
    
    #
    # Store in the database.
    #
    DB.storeImg(resized_img_path, flight_data_path)
    
    #
    # Send the new image and flight_data
    #
    with open(resized_img_path, 'rb') as f:
        data = [os.path.split(resized_img_path)[-1], f.read(), json.dumps(flight_data)]
    
    try:
        zmq_socket.push(data)
        log.msg("Finished sending of {img}.".format(img=resized_img_name))
        
    except zmq.error.Again:
        log.msg("Skipping sending of {img}, no pull consumers...".format(img=resized_img_name))


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
        
        d = threads.deferToThread(handleNewImage, path)


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
    log.addObserver(log.defaultObserver._emit)
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
    # Setup the zmq socket used for sending images.
    #
    global zmq_socket
    zmq_factory = ZmqFactory()
    endpoint = ZmqEndpoint('connect', 'tcp://localhost:8888')
    zmq_socket = ZmqPushConnection(zmq_factory, endpoint)
    
    #
    # Startup the reactor.
    #
    reactor.listenTCP(port, factory)
    reactor.run()
