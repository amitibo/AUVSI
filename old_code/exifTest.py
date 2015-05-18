__author__ = 'Ori'
import pyexiv2

source_filename = r'C:\Users\Ori\Downloads\exivTest\testing.jpg'
destination_filename = r'C:\Users\Ori\Downloads\exivTest\resized.jpg'

m1 = pyexiv2.ImageMetadata( source_filename )
m1.read()
# modify tags ...
# m1['Exif.Image.Key'] = pyexiv2.ExifTag('Exif.Image.Key', 'value')
m1.modified = True # not sure what this is good for
m2 = pyexiv2.metadata.ImageMetadata( destination_filename )
m2.read() # yes, we need to read the old stuff before we can overwrite it
m1.copy( m2 )
m2.write()