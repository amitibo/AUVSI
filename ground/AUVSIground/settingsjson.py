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