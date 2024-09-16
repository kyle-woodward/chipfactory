import rasterio as rio
from rasterio.io import MemoryFile
import numpy as np
import os
from pprint import pprint

def to_geotiff(data, output_path, **kwargs):
    """Write numpy ndarray to a GeoTIFF file"""
    if not output_path.endswith('.tif'):
        output_path = output_path + '.tif'
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    height, width = data.shape
    bands = len(data[0][0])
    print('bands length',bands)
    print('dtpye',data.dtype)
    with rio.open(output_path, 
                  'w', 
                  driver='GTiff', 
                  count=bands, 
                  height=height, 
                  width=width, 
                  dtype='uint16') as dst:
        dst.write(data, 1)


def to_npy(data, output_path, **kwargs):
    np.save(os.path.join(output_path,'test.npy'), data)

def to_tfrecord(data, output_path, **kwargs):
    pass

def blob_upload(data, output_path, **kwargs):
    """Upload data to blob storage (GCS, S3, etc)"""
    pass

def bytes_to_tiff(response,output_path,**kwargs):
    with MemoryFile(response) as memfile:
        with memfile.open() as dataset:
            with rio.open(os.path.join(output_path,'output.tif'), 'w', **dataset.profile) as dst:
                dst.write(dataset.read())