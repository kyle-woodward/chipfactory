from src.ChipFactory import ChipFactoryEE
import ee
ee.Initialize()

def test_chip_ee_gtiff():
    """Test ChipFactoryEE"""
    # Test ChipFactoryEE
    image = 'GOOGLE/DYNAMICWORLD/V1/20220108T160639_20220108T160732_T17SQB'
    chip_locations = (ee.FeatureCollection.randomPoints(ee.Image(image).geometry(), 5, 42, 0.001)
                      .geometry().getInfo()['coordinates'])    
    
    output_location = r"C:\Users\kyle\Downloads\chip_tests"
    output_type = 'GEO_TIFF'
    cloud_project = 'pc511-gambia-training'
    
    chipper = ChipFactoryEE(image, 
                            chip_locations, 
                            output_location, 
                            output_type, 
                            cloud_project)
    chipper.check_image()
    bands = chipper.list_bands()
    expected_bands = ['water', 'trees', 'grass', 
                      'flooded_vegetation', 'crops', 'shrub_and_scrub', 
                      'built', 'bare', 'snow_and_ice', 'label']
    assert bands == expected_bands, "Bands not as expected"
    
    chipper.chip(bands=bands, 
                 scale=10, 
                 crs='EPSG:4326', 
                 chip_x=256, 
                 chip_y=256, 
                 workload_tag='test') 
test_chip_ee_gtiff()

def test_chip_ee_npy():
    """Test ChipFactoryEE"""
    # Test ChipFactoryEE
    image = 'GOOGLE/DYNAMICWORLD/V1/20220108T160639_20220108T160732_T17SQB'
    chip_locations = (ee.FeatureCollection.randomPoints(ee.Image(image).geometry(), 5, 42, 0.001)
                      .geometry().getInfo()['coordinates'])  
    
    output_location = r"C:\Users\kyle\Downloads\chip_tests"
    output_type = 'NPY'
    cloud_project = 'pc511-gambia-training'
    
    chipper = ChipFactoryEE(image, 
                            chip_locations, 
                            output_location, 
                            output_type, 
                            cloud_project)
    chipper.check_image()
    bands = chipper.list_bands()
    expected_bands = ['water', 'trees', 'grass', 
                      'flooded_vegetation', 'crops', 'shrub_and_scrub', 
                      'built', 'bare', 'snow_and_ice', 'label']
    assert bands == expected_bands, "Bands not as expected"
    
    chipper.chip(bands=bands, 
                 scale=10, 
                 crs='EPSG:4326', 
                 chip_x=256, 
                 chip_y=256, 
                 workload_tag='test')
test_chip_ee_npy()

def test_chip_ee_gtiff_private():
    image = "projects/pc511-gambia-training/assets/Pleiades_RGB_composite"
    chip_locations = (ee.FeatureCollection.randomPoints(ee.Image(image).geometry(), 5, 42, 0.001)
                      .geometry().getInfo()['coordinates']) 
    my_factory = ChipFactoryEE(image,
                                chip_locations, 
                                r"C:\Users\kyle\Downloads\chip_tests_private", 
                                "GEO_TIFF",
                                "pc511-gambia-training")
    my_factory.check_image()

    my_factory.chip(['b1', 'b2', 'b3'],  
                 scale=1, 
                 crs='EPSG:4326',
                 chip_x=256, 
                 chip_y=256,
                 workload_tag='test-chipfactory-ee',
                 request_limit=20)
    
test_chip_ee_gtiff_private()

