from __future__ import division
from twisted.internet import reactor, protocol, task, threads
from sortedcontainers import SortedDict
from twisted.python import log
from datetime import datetime
import global_settings as gs
try:
    from pymavlink import mavutil
except:
    pass
import json
import os


TIMESTAMP_SIGNATURE = "%Y_%m_%d_%H_%M_%S_%f"


def wait_heartbeat(m):
    """wait for a heartbeat so we know the target system IDs"""
    
    log.msg("Waiting for APM heartbeat")
    m.wait_heartbeat()
    log.msg("Heartbeat from APM (system %u component %u)" % (m.target_system, m.target_system))


continue_messages = True

def monitorMessages(m):
    """show incoming mavlink messages"""
    
    flight_data = {}
    while continue_messages:
        msg = m.recv_match(blocking=True)
        if not msg or msg.get_type() == "BAD_DATA":
            continue
        
        if msg.get_type() == "ATTITUDE":
            flight_data['yaw'] = msg.yaw
            flight_data['roll'] = msg.roll
            flight_data['pitch'] = msg.pitch
        elif msg.get_type() == "GLOBAL_POSITION_INT":
            t = datetime.now()
            flight_data['timestamp'] = t.strftime(TIMESTAMP_SIGNATURE)
            flight_data['lon'] = msg.lon
            flight_data['lat'] = msg.lat
            flight_data['relative_alt'] = msg.relative_alt
          
            if 'yaw' in flight_data:
                path = os.path.join(gs.FLIGHT_DATA_FOLDER, "{timestamp}.json".format(timestamp=flight_data['timestamp']))
                with open(path, 'wb') as f:
                    json.dump(flight_data, f)

                reactor.callFromThread(addPHdata, flight_data)
                flight_data = {}


def addPHdata(flight_data):
    """Add new flight data message to the records"""
    
    global flight_data_log
    
    flight_data_log[flight_data['timestamp']] = flight_data


def queryPHdata(timestamp):
    """Query the closest flight data records to some timestamp"""
    
    index = flight_data_log.bisect(timestamp)
    
    r_index = max(index-1, 0)
    l_index = min(index, len(flight_data_log))
    
    #
    # TODO interpolate the sorrounding flight data records.
    #
    return flight_data_log.values()[r_index]#, flight_data_log.values()[l_index]


def initPixHawk(device='/dev/ttyUSB0', baudrate=57600, rate=4):
    """Start the thread that monitors the PixHawk Mavlink messages.
    
    Parameters
    ----------
    device: str
        Address of serialport device.
    baudrate: int
        Serialport baudrate (defaults to 57600)
    rate: int
        Requested rate of messages.
    """
    
    global flight_data_log
    
    flight_data_log = SortedDict()

    #
    # Create the auvsi data folder.
    #
    if not os.path.exists(gs.AUVSI_BASE_FOLDER):
        os.makedirs(gs.AUVSI_BASE_FOLDER)
    if not os.path.exists(gs.FLIGHT_DATA_FOLDER):
        os.makedirs(gs.FLIGHT_DATA_FOLDER)
        
    #
    # create a mavlink serial instance
    #    
    master = mavutil.mavlink_connection(device, baud=baudrate)
    
    #
    # wait for the heartbeat msg to find the system ID
    #
    wait_heartbeat(master)
    
    #
    # Setting requested streams and their rate.
    #
    log.msg("Sending all stream request for rate %u" % rate)
    for i in range(3):
        master.mav.request_data_stream_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL,
            rate,
            1
        )
    
    #
    # Start the messages thread
    #
    d = threads.deferToThread(monitorMessages, master)


def initPixHawkSimulation():
    import glob
    
    global flight_data_log
    
    flight_data_log = SortedDict()

    base_path = os.environ['AUVSI_CV_DATA']
    log_paths = glob.glob(os.path.join(base_path, 'flight_data', '*.json'))

    for path in sorted(log_paths):
        with open(path, 'rb') as f:
            addPHdata(json.load(f))
            

def stopPixHawk():
    
    global continue_messages
    
    continue_message = False


if __name__ == '__main__':

    #try:
        #initPixHawk()
        #reactor.run()
    #except:
        #stopPixHawk()
        #raise

    import AUVSIcv
    
    initPixHawkSimulation()
    
    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

    
    img = AUVSIcv.Image(imgs_paths[0])
    print queryPHdata(img.datetime)
