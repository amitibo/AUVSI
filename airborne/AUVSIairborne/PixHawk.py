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
import glob
from bisect import bisect


TIMESTAMP_SIGNATURE = gs.BASE_TIMESTAMP


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
                addPHdata(flight_data)

                flight_data = {}


def addPHdata(flight_data):
    path = os.path.join(gs.FLIGHT_DATA_FOLDER, "{timestamp}.json"
                        .format(timestamp=flight_data['timestamp']))
    with open(path, 'wb') as f:
        json.dump(flight_data, f)



def queryPHdata(timestamp):
    """Query the closest flight data records to some timestamp"""

    flight_data_list = sorted(os.listdir(gs.FLIGHT_DATA_FOLDER))
    index = bisect(flight_data_list, timestamp)
    
    r_index = max(index-1, 0)
    l_index = min(index, len(flight_data_list))

    data_path = os.path.join(gs.FLIGHT_DATA_FOLDER, flight_data_list[r_index])

    #
    # TODO interpolate the sorrounding flight data records.
    #
    with open(data_path, 'rb') as f:
        data = json.load(f)

    return data


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

    _create_database()

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


def _create_database():
    #
    # Create the auvsi data folder.
    #
    if not os.path.exists(gs.AUVSI_BASE_FOLDER):
        os.makedirs(gs.AUVSI_BASE_FOLDER)
    if not os.path.exists(gs.FLIGHT_DATA_FOLDER):
        os.makedirs(gs.FLIGHT_DATA_FOLDER)


def initPixHawkSimulation():
    import glob

    _create_database()

    data_paths = os.path.join(gs.SIMULATION_DATA,
                              'flight_data', '*.json')
    log_paths = glob.glob(data_paths)

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
    
    base_path = os.path.join(gs.SIMULATION_DATA, 'renamed_images')
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

    print imgs_paths[0]
    img = AUVSIcv.Image(imgs_paths[0])
    print queryPHdata(img.datetime)
