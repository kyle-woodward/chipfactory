import pickle
import ee
import src.postprocessors as pp
class ChipFactory:
    def __init__(self, image, chip_locations, output_location, output_type):
        self.IMAGE = image # image source (ee.Image, STAC)
        self.CHIP_LOCATIONS = chip_locations # lat, lon points structured as [tuple(lat, lon)]
        self.OUTPUT_LOCATION = output_location # output location for chips
        self.OUTPUT_TYPE = output_type # ZARR, GTiff, TFRecord, etc

    def check_chip_locations(self):
        """check that chip locations are valid"""
        valid = isinstance(
            self.CHIP_LOCATIONS, list)
        assert valid, "Chip Locations must be a list of lat,lon tuples"
    
    def pickle_check(self):
        """check that materials are picklable for any distributed processing"""
        try:
            pickle.dump(self, open("chip_factory.pickle", "wb"))
        except pickle.PicklingError as e:
            print(f"Error occurred while pickling: {e}")
    
    def chip(self):
        """Validates Image and Chip Locations, then Runs Chipper"""
        self.pickle_check()
        self.check_chip_locations
        self.chip()
    
class ChipFactoryEE(ChipFactory):
    from multiprocessing import Pool
    from functools import partial
    def __init__(self, image, chip_locations, output_location, output_type, cloud_project):
        super().__init__(image, chip_locations, output_location, output_type)

        self.INIT_PARAMS = dict(
        project=cloud_project,
        opt_url=ee.data.HIGH_VOLUME_API_BASE_URL)

        ee.Initialize(**self.INIT_PARAMS)
    
    def check_image(self):
        """check that the image is accessible"""
        try:
            ee.Image(self.IMAGE).getInfo()
        except Exception as e:
            print(f"Error occurred while accessing image: {e}")
    
    def list_bands(self):
        """list bands in image"""
        bands = ee.Image(self.IMAGE).bandNames().getInfo()
        return bands
    
    def chip(self, 
             bands:list, 
             scale:int, 
             crs:str='EPSG:4326',
             chip_x:int=256, 
             chip_y:int=256,
             workload_tag:str='test',
             request_limit:int=20):
        
        print('running EE specific chipper')
        
        # Factory Level Variables for all chipping requests
        proj = ee.Projection(crs).atScale(scale).getInfo()
        
        factory_settings = {
         'image': self.IMAGE,
         'bands': bands,
         'coord_list':self.CHIP_LOCATIONS,
         'proj': proj,
         'scale_x': proj['transform'][0],
         'scale_y': -proj['transform'][4],
         'output_type': self.OUTPUT_TYPE,
        'chip_x': chip_x,
        'chip_y': chip_y,
        'workload_tag': workload_tag,
        'request_limit': request_limit
        }
        
        # native_supported_formats = ["NUMPY_NDARRAY",
        #                             "IMAGE_FILE_FORMAT_UNSPECIFIED",
        #                             "GEO_TIFF", 
        #                             "NPY", 
        #                             "TF_RECORD_IMAGE"] # plus a few others not relevant
        # if self.OUTPUT_TYPE not in native_supported_formats:
        #     raise ValueError(f"Output Type {self.OUTPUT_TYPE} not supported. ",
        #                      f"Supported formats: {native_supported_formats}")
        
        def construct_request(coords, **kwargs):
            # Make a request object.
            request = {
                'expression': ee.Image(kwargs.get('image')),
                'fileFormat': kwargs.get('output_type'),
                'bandIds': kwargs.get('bands'),
                'grid': {
                    'dimensions': {
                        'width': kwargs.get('chip_x'),
                        'height': kwargs.get('chip_y')
                    },
                    'affineTransform': {
                        'scaleX': kwargs.get('scale_x'),
                        'shearX': 0,
                        'translateX': coords[0],
                        'shearY': 0,
                        'scaleY': kwargs.get('scale_y'),
                        'translateY': coords[1]
                    },
                    'crsCode': kwargs.get('proj')['crs'],
                },
                'workloadTag': kwargs.get('workload_tag'),
            }

            return request
        
        def process_request(coords,*args):
            file_processors = {
                # 'NUMPY_NDARRAY': pp.to_npy, 
                'GEO_TIFF': pp.bytes_to_tiff, # testing
                'NPY': pp.to_npy, # works when request is format NPY
                # 'TF_RECORD_IMAGE': pp.to_tfrecord
                }
            
            # Construct the request for the current coords
            request = construct_request(coords, **factory_settings)

            # Send the request and process the response
            response = ee.data.computePixels(request)

            file_processor = file_processors[self.OUTPUT_TYPE]
            file_processor(response, self.OUTPUT_LOCATION, *args)
            
            return response
        
        
        index = [f'chip_{i:03}' for i in range(len(self.CHIP_LOCATIONS))]
        zipped = zip(index,self.CHIP_LOCATIONS)
        for index,coords in zipped:
            # Process the response according to defined output type
            process_request(coords, index)
        

class ChipFactorySTAC(ChipFactory):
    def __init__(self, image, chip_locations, product, *args): # any other auth requirements?
        super().__init__(image, chip_locations, product)

    def check_image(self):
        """check that the image is accessible"""
        pass

    def list_bands(self):
        """list bands in image"""
        pass

    def chip(self):
        print('running STAC specific chipper')
        pass

class ChipFactoryLocal(ChipFactory):
    def __init__(self, image, chip_locations, output_location, output_type, *args):
        super().__init__(image, chip_locations, output_location, output_type)

    def check_image(self):
        """check that the image is accessible"""
        pass

    def list_bands(self):
        """list bands in image"""
        pass

    def chip(self):
        print('running Local specific chipper')