import pickle
import ee
import postprocessors as pp
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
             workoad_tag:str='test',
             request_limit:int=20):
        
        print('running EE specific chipper')

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
        
        def process_request(coords):
            # Construct the request for the current coords
            request = construct_request(coords, 
                                        **factory_settings)

            # Send the request and process the response
            response = ee.data.computePixels(request)

            # Process the response as needed
            # ...
            return response
        
        
        # Factory Level Variables for all chipping requests
        proj = ee.Projection(crs).atScale(scale).getInfo()
        factory_settings = {
         'image': self.IMAGE,
         'bands': bands,
         'coord_list':self.CHIP_LOCATIONS,
         'proj': proj,
         'scale_x': proj['transform'][0],
         'scale_y': -proj['transform'][4],
         'output_type': "NUMPY_NDARRAY",#self.OUTPUT_TYPE,
        'chip_x': chip_x,
        'chip_y': chip_y,
        'workload_tag': workoad_tag,
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

        processors = {'NUMPY_NDARRAY': pp.to_npy,
         'GEO_TIFF': pp.to_geotiff,
         'NPY': pp.to_npy,
         'TF_RECORD_IMAGE': pp.to_tfrecord}
        
        for coords in self.CHIP_LOCATIONS:
            # Process the response according to defined output type
            response = process_request(coords)
            processor = processors[self.OUTPUT_TYPE]
            processor(response, self.OUTPUT_LOCATION, **factory_settings)
            break
        

class ChipFactorySTAC(ChipFactory):
    def __init__(self, image, chip_locations, product): # any other auth requirements?
        super().__init__(image, chip_locations, product)

    def check_image(self):
        """check that the image is accessible"""
        pass
    
    def chip(self):
        print('running STAC specific chipper')
    
    def run(self):
        """Checks Materials and Runs Extractor"""
        print('running STAC specific extractor')

# testing
img = "projects/pc511-gambia-training/assets/Pleiades_RGB_composite"
points = [(-16.7021, 13.3686)]
my_factory = ChipFactoryEE(img,
                            points, 
                            r"C:\Users\kyle\Downloads\chip_tests", 
                            "GEO_TIFF",
                            "pc511-gambia-training")

print(my_factory.IMAGE)
print(my_factory.CHIP_LOCATIONS)
print(my_factory.OUTPUT_LOCATION)
print(my_factory.OUTPUT_TYPE)
print(my_factory.INIT_PARAMS)
print(my_factory.list_bands())

my_factory.chip(['b1', 'b2', 'b3'],  
             scale=1, 
             crs='EPSG:4326',
             chip_x=256, 
             chip_y=256,
             workoad_tag='test-chipfactory-ee',
             request_limit=20)

# my_factory.OUTPUT_TYPE = "GEO_TIFF"
# my_factory.chip(['b1', 'b2', 'b3'],  
#              scale=1, 
#              crs='EPSG:4326',
#              chip_x=5, 
#              chip_y=5,
#              workoad_tag='test-chipfactory-ee',
#              request_limit=20)

# my_factory.OUTPUT_TYPE = "NPY"
# my_factory.chip(['b1', 'b2', 'b3'],  
#              scale=1, 
#              crs='EPSG:4326',
#              chip_x=256, 
#              chip_y=256,
#              workoad_tag='test-chipfactory-ee',
#              request_limit=20)