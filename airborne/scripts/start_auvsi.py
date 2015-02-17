from __future__ import division
from AUVSIairborne import start_server
import argparse


def main(camera_type, port):
    
    start_server(camera_type=camera_type, port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the airborne server.')
    parser.add_argument('--camera', type=str, default='canon', help='Camera type. Options: [canon (default), simlulation].')
    parser.add_argument('--port', type=int, default=8000, help='Server port (default=8000).')
    args = parser.parse_args()
    
    main(camera_type=args.camera, port=args.port)
    
