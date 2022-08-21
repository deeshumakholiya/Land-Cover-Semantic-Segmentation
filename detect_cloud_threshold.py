#from PIL import Image
from osgeo import gdal
from osgeo import osr
import numpy as np

#setting
src_filename = 'cloud_c_22.tif'
dst_filename = 'mask_cloud/cloud_c_22.tif'

ds = gdal.Open(src_filename)
band = ds.GetRasterBand(1) #matrix band for tif file
gt = ds.GetGeoTransform() #info about geo (used for metadata)
array_band = np.array(band.ReadAsArray())
ysize, xsize = np.shape(array_band)

channel_out = np.zeros(np.shape(array_band)) #same size matrix with value 0
channel_out[array_band >= 240] = 1 #threshold

fileformat = "GTiff"
driver = gdal.GetDriverByName(fileformat)
dst_ds = driver.Create(dst_filename, xsize=xsize, ysize=ysize, bands=1, eType=gdal.GDT_Byte)

#write data for metadata and georefrencing
dst_ds.SetGeoTransform(gt)
wgs84_wkt = """
PROJCRS["WGS_1984_UTM_Zone_33N",
    BASEGEOGCRS["WGS 84",
        DATUM["World Geodetic System 1984",
            ELLIPSOID["WGS 84",6378137,298.257223563,
                LENGTHUNIT["metre",1]]],
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433]],
        ID["EPSG",4326]],
    CONVERSION["Transverse Mercator",
        METHOD["Transverse Mercator",
            ID["EPSG",9807]],
        PARAMETER["Latitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",15,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["Scale factor at natural origin",0.9996,
            SCALEUNIT["unity",1],
            ID["EPSG",8805]],
        PARAMETER["False easting",500000,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]]],
    CS[Cartesian,2],
        AXIS["(E)",east,
            ORDER[1],
            LENGTHUNIT["metre",1]],
        AXIS["(N)",north,
            ORDER[2],
            LENGTHUNIT["metre",1]],
    ID["EPSG",32633]]
"""

srs = osr.SpatialReference() 
srs.ImportFromWkt(wgs84_wkt)
srs.SetUTM(33, 1)
srs.SetWellKnownGeogCS("WGS84")
dst_ds.SetProjection(srs.ExportToWkt())
dst_ds.GetRasterBand(1).WriteArray(channel_out)
# Once we're done, close properly the dataset
dst_ds = None