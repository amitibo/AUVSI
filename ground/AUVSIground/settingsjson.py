__author__ = 'Ori'


import json

network_json = json.dumps(
    [
        {'type': 'title',
         'title': 'Airborne Server'},
        {'type': 'string',
         'title': 'IP',
         'desc': 'IP address or HOSTNAME of airborne server',
         'section': 'Network',
         'key': 'ip'},
        {'type': 'numeric',
         'title': 'port',
         'desc': 'Port number of the airborne server',
         'section': 'Network',
         'key': 'port'},

        {'type': 'title',
         'title': 'GS Settings'},
        {'type': 'string',
         'title': "GS' Database Path",
         'desc': "The path to the GS' DB, could be ftp in future",
         'section': "GS' Database",
         'key': 'path'}
    ]
)

camera_json = json.dumps(
    [
        {'type': 'title',
         'title': 'Camera Settings'},
        {'type': 'numeric',
         'title': 'ISO',
         'desc': 'ISO settings of camera',
         'section': 'Camera',
         'key': 'iso'},
        {'type': 'numeric',
         'title': 'Shutter',
         'desc': 'Shutter speed settings of camera (=1/value)',
         'section': 'Camera',
         'key': 'shutter'},
        {'type': 'numeric',
         'title': 'Aperture',
         'desc': 'Aperture settings of camera',
         'section': 'Camera',
         'key': 'aperture'},
        {'type': 'numeric',
         'title': 'Zoom',
         'desc': 'Zoom settings of camera',
         'section': 'Camera',
         'key': 'zoom'},
    ]
)

cv_json = json.dumps(
    [
        {'type': 'title',
         'title': 'Image Processing'},
        {'type': 'numeric',
         'title': 'Image Rescaling',
         'desc': 'Rate of image rescaling for transmission',
         'section': 'CV',
         'key': 'image_rescaling'},
    ]
)

