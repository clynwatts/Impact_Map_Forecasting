import os
import json
import rasterio.warp
import logging
import numpy as np
import rasterio
from osgeo import gdal, ogr, osr

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

impact_folder = config['impact_folder']
output_path = config['output_path']
svi_folder = config['svi_folder']
depth_path = os.path.join(output_path, "d_discharge_12040104_0.tif")
svi_raster_path = os.path.join(svi_folder, "SVI.tif")
aligned_svi_raster_path = os.path.join(impact_folder, "aligned_svi_raster.tif")

# Function to reproject and resample raster
def reproject_resample_raster(input_path, reference_path, output_path):
    with rasterio.open(reference_path) as ref_src:
        ref_transform = ref_src.transform
        ref_crs = ref_src.crs
        ref_width = ref_src.width
        ref_height = ref_src.height
        ref_res = ref_src.res
    with rasterio.open(input_path) as src:
        transform, width, height = rasterio.warp.calculate_default_transform(
            src.crs, ref_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': ref_crs,
            'transform': transform,
            'width': ref_width,
            'height': ref_height,
            'res': ref_res,
            'nodata': -9999
        })
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                rasterio.warp.reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=ref_crs,
                    resampling=rasterio.enums.Resampling.bilinear)

try:
    # Reproject and resample SVI raster to match the WaterDepth raster
    logging.info("Reprojecting and resampling SVI raster")
    reproject_resample_raster(svi_raster_path, depth_path, aligned_svi_raster_path)
    logging.info("Reprojection and resampling completed successfully")
except Exception as e:
    logging.error(f"An error occurred during the reprojection and resampling process: {e}")

import numpy as np
import rasterio

reclassified_depth_path = os.path.join(impact_folder, "reclassified_depth.tif")

# Function to reclassify raster
def reclassify_raster(input_path, output_path, bins, nodata_value=-9999):
    with rasterio.open(input_path) as src:
        data = src.read(1).astype('float32')
        nodata = src.nodata
        if nodata is not None:
            data = np.ma.masked_equal(data, nodata)
        reclassified_data = np.digitize(data, bins=bins, right=True)
        reclassified_data = np.where(data == 0, 0, reclassified_data)
        reclassified_data = np.ma.filled(reclassified_data, nodata)
        meta = src.meta
        meta.update(dtype='float32', nodata=nodata_value)
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(reclassified_data.astype('float32'), 1)

try:
    # Reclassify the WaterDepth raster
    logging.info("Reclassifying WaterDepth raster")
    reclassify_raster(depth_path, reclassified_depth_path, bins=[0.01, 0.4, 0.8, 1.8])
    logging.info("Reclassification completed successfully")
except Exception as e:
    logging.error(f"An error occurred during the reclassification process: {e}")


impact_raster_path = os.path.join(impact_folder, "Initial_Impact_map.tif")

# Function to multiply rasters
def multiply_rasters(svi_path, depth_path, output_path, nodata_value=-9999):
    with rasterio.open(svi_path) as svi_src:
        svi_data = svi_src.read(1).astype('float32')
        svi_nodata = svi_src.nodata
    with rasterio.open(depth_path) as depth_src:
        depth_data = depth_src.read(1).astype('float32')
        depth_meta = depth_src.meta
        depth_nodata = depth_src.nodata
    if svi_data.shape != depth_data.shape:
        raise ValueError("The rasters do not have the same shape.")
    svi_data = np.where(svi_data == svi_nodata, np.nan, svi_data)
    depth_data = np.where(depth_data == depth_nodata, np.nan, depth_data)
    impact_data = np.where(np.isnan(svi_data) | np.isnan(depth_data), nodata_value, svi_data * depth_data)
    impact_meta = depth_meta.copy()
    impact_meta.update({'dtype': 'float32', 'nodata': nodata_value})
    with rasterio.open(output_path, 'w', **impact_meta) as impact_dst:
        impact_dst.write(impact_data.astype('float32'), 1)

try:
    # Multiply the aligned SVI and reclassified WaterDepth rasters
    logging.info("Multiplying SVI and reclassified WaterDepth rasters")
    multiply_rasters(aligned_svi_raster_path, reclassified_depth_path, impact_raster_path)
    logging.info("Multiplication completed successfully")
except Exception as e:
    logging.error(f"An error occurred during the multiplication process: {e}")



masked_impact_raster_path = os.path.join(impact_folder, "masked_Impact_map.tif")

# Function to mask zeros in raster
def mask_zeros(input_path, output_path):
    with rasterio.open(input_path) as src:
        data = src.read(1).astype('float32')
        nodata = src.nodata
        masked_data = np.where(data == 0, nodata, data)
        meta = src.meta
        meta.update(dtype='float32', nodata=nodata)
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(masked_data.astype('float32'), 1)

try:
    # Mask zeros in the impact raster
    logging.info("Masking zeros in the impact raster")
    mask_zeros(impact_raster_path, masked_impact_raster_path)
    logging.info("Masking completed successfully")
except Exception as e:
    logging.error(f"An error occurred during the masking process: {e}")
classified_impact_raster_path = os.path.join(impact_folder, "reclass_Impact_map.tif")

# Function to classify raster
def classify_raster(input_path, output_path):
    with rasterio.open(input_path) as src:
        data = src.read(1).astype('float32')
        nodata = src.nodata
        data_masked = np.ma.masked_equal(data, nodata)
        min_value = data_masked.min()
        max_value = data_masked.max()
        bins = np.linspace(min_value, max_value, 4)
        classified_data = np.digitize(data_masked, bins, right=True)
        classified_data[data_masked.mask] = nodata
        meta = src.meta
        meta.update(dtype='float32', nodata=nodata)
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(classified_data.astype('float32'), 1)

try:
    # Classify the impact raster
    logging.info("Classifying the impact raster")
    classify_raster(masked_impact_raster_path, classified_impact_raster_path)
    logging.info("Classification completed successfully")
except Exception as e:
    logging.error(f"An error occurred during the classification process: {e}")

import os
import json
from osgeo import gdal, ogr, osr
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

impact_folder = config['impact_folder']
classified_impact_raster_path = os.path.join(impact_folder, "reclass_Impact_map.tif")
shapefile_path = os.path.join(impact_folder, "reclass_Impact_map.shp")

# Function to convert raster to shapefile
def raster_to_shapefile(raster_path, shapefile_path):
    src_ds = gdal.Open(raster_path)
    if src_ds is None:
        raise RuntimeError(f"Failed to open raster {raster_path}")
    
    src_band = src_ds.GetRasterBand(1)
    nodata = src_band.GetNoDataValue()
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if driver is None:
        raise RuntimeError("ESRI Shapefile driver not available.")
    
    dst_ds = driver.CreateDataSource(shapefile_path)
    if dst_ds is None:
        raise RuntimeError(f"Failed to create shapefile {shapefile_path}")
    
    srs = osr.SpatialReference()
    srs.ImportFromWkt(src_ds.GetProjection())
    
    dst_layer = dst_ds.CreateLayer('impact', srs=srs, geom_type=ogr.wkbPolygon)
    if dst_layer is None:
        raise RuntimeError(f"Failed to create layer in shapefile {shapefile_path}")
    
    field_defn = ogr.FieldDefn('FIV_Class', ogr.OFTInteger)
    dst_layer.CreateField(field_defn)
    
    gdal.Polygonize(src_band, src_band.GetMaskBand(), dst_layer, 0, options=["8CONNECTED=8"], callback=None)
    
    # Remove polygons where FIV_Class is equal to nodata value
    dst_layer.SetAttributeFilter(f"FIV_Class = {int(nodata)}")
    for feature in dst_layer:
        dst_layer.DeleteFeature(feature.GetFID())
    dst_layer.SetAttributeFilter(None)
    
    src_ds = None
    dst_ds = None

try:
    logging.info("Converting classified impact map to shapefile")
    raster_to_shapefile(classified_impact_raster_path, shapefile_path)
    logging.info("Conversion to shapefile completed successfully")
except Exception as e:
    logging.error(f"An error occurred during the conversion process: {e}")


import os
import json
from osgeo import gdal, ogr, osr
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

impact_folder = config['impact_folder']
classified_impact_raster_path = os.path.join(impact_folder, "reclass_Impact_map.tif")
shapefile_path = os.path.join(impact_folder, "reclass_Impact_map.shp")

# Function to convert raster to shapefile
def raster_to_shapefile(raster_path, shapefile_path):
    src_ds = gdal.Open(raster_path)
    if src_ds is None:
        raise RuntimeError(f"Failed to open raster {raster_path}")
    
    src_band = src_ds.GetRasterBand(1)
    nodata = src_band.GetNoDataValue()
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if driver is None:
        raise RuntimeError("ESRI Shapefile driver not available.")
    
    dst_ds = driver.CreateDataSource(shapefile_path)
    if dst_ds is None:
        raise RuntimeError(f"Failed to create shapefile {shapefile_path}")
    
    srs = osr.SpatialReference()
    srs.ImportFromWkt(src_ds.GetProjection())
    
    dst_layer = dst_ds.CreateLayer('impact', srs=srs, geom_type=ogr.wkbPolygon)
    if dst_layer is None:
        raise RuntimeError(f"Failed to create layer in shapefile {shapefile_path}")
    
    field_defn = ogr.FieldDefn('FIV_Class', ogr.OFTInteger)
    dst_layer.CreateField(field_defn)
    
    gdal.Polygonize(src_band, src_band.GetMaskBand(), dst_layer, 0, options=["8CONNECTED=8"], callback=None)
    
    # Remove polygons where FIV_Class is equal to nodata value
    dst_layer.SetAttributeFilter(f"FIV_Class = {int(nodata)}")
    for feature in dst_layer:
        dst_layer.DeleteFeature(feature.GetFID())
    dst_layer.SetAttributeFilter(None)
    
    src_ds = None
    dst_ds = None

# Function to add vulnerability column to shapefile
def add_vulnerability_column(shapefile_path):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(shapefile_path, 1)
    layer = ds.GetLayer()
    vulnerability_field = ogr.FieldDefn('Vuln_Level', ogr.OFTString)
    vulnerability_field.SetWidth(32)
    layer.CreateField(vulnerability_field)
    
    # Define vulnerability levels
    vulnerability_levels = {
        0: "Low",
        1: "Medium",
        2: "High",
        3: "Very High"
    }
    
    # Update the new field based on FIV_Class
    for feature in layer:
        fiv_class = feature.GetField('FIV_Class')
        vulnerability_level = vulnerability_levels.get(fiv_class, "Unknown")
        feature.SetField('Vuln_Level', vulnerability_level)
        layer.SetFeature(feature)
    
    ds = None
    print("Vulnerability level column has been added to the shapefile.")

try:
    logging.info("Converting classified impact map to shapefile")
    raster_to_shapefile(classified_impact_raster_path, shapefile_path)
    logging.info("Conversion to shapefile completed successfully")
    
    logging.info("Adding vulnerability level column to shapefile")
    add_vulnerability_column(shapefile_path)
    logging.info("Vulnerability level column added successfully")

except Exception as e:
    logging.error(f"An error occurred during the processing: {e}")
