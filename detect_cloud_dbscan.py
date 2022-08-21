#from PIL import Image
from osgeo import gdal
from osgeo import osr
import numpy as np
from sklearn.cluster import DBSCAN


#setting
in_filename = 'cloud_c_11.tif'
out_filename = 'mask_cloud_ml/cloud_c_11.tif'

ds = gdal.Open(in_filename)
gt = ds.GetGeoTransform()
band = ds.GetRasterBand(1).ReadAsArray()

array_band = np.array(band)

channel_out = np.zeros(np.shape(array_band))
channel_out[array_band >= 240] = 1

len_ver, len_hor = np.shape(channel_out)
sec_len_ver = np.linspace(0, len_ver, 10).astype(int) #particion the file into 9x9=81 parts
sec_len_hor = np.linspace(0, len_hor, 10).astype(int)


array_new = np.zeros((len_ver, len_hor))
for i in range(len(sec_len_ver)-1):
    for j in range(len(sec_len_hor)-1):
        print('process %s , %s'%(i+1, j+1)) 
        section = channel_out[sec_len_ver[i]: sec_len_ver[i+1], sec_len_hor[j]: sec_len_hor[j+1]]
        print(np.sum(section), np.shape(section)[0]*np.shape(section)[1]) #data >=240
        if np.all(section == 1):
            print('immediately fill matrix')
            array_new[sec_len_ver[i]:sec_len_ver[i]+np.shape(section)[0]-1, sec_len_hor[j]+np.shape(section)[1]-1] = 1
            continue
        all_idx_cloud = np.where(section == 1)
        all_idx_cloud = np.transpose(all_idx_cloud)
        try:
            db = DBSCAN(eps=4, min_samples=30).fit(all_idx_cloud)
        except ValueError:
            continue
        for k in range(len(db.labels_)):
            if db.labels_[k] == -1: #outlier for dbscan(large building,high albedo)
                continue
            array_new[sec_len_ver[i]+all_idx_cloud[k,0], sec_len_hor[j]+all_idx_cloud[k,1]] = 1
        print(np.shape(db.labels_[db.labels_ != -1]), np.shape(all_idx_cloud))
        

#write data for metadata and georefrencing
fileformat = "GTiff"
driver = gdal.GetDriverByName(fileformat)
dst_ds = driver.Create(out_filename, xsize=len_hor, ysize=len_ver, bands=1, eType=gdal.GDT_Byte)

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
dst_ds.GetRasterBand(1).WriteArray(array_new)
# Once we're done, close properly the dataset
dst_ds = None

