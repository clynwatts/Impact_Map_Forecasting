import os
import json
import numpy as np
import rasterio
import rasterio.features
from rasterio.enums import Resampling
import logging
from scipy.ndimage import gaussian_filter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

depth_folder = config['depth_folder']
output_path = config['output_path']
dem_path = os.path.join(depth_folder, "DEM", "Houston_DEM.tif")
original_inundation_path = os.path.join(output_path, "i_discharge_12040104_0.tif")
reclassified_inundation_path = os.path.join(depth_folder, "reclassified_inundation.tif")
WaterDepthOutput = os.path.join(depth_folder, "WaterDepth_output.tif")

logging.info("Starting water depth estimation process")

try:
    # Load DEM
    logging.info("Loading DEM")
    with rasterio.open(dem_path) as dem:
        dem_data = dem.read(1, masked=True)
        dem_transform = dem.transform
        dem_crs = dem.crs
        dem_profile = dem.profile

    # Load original inundation raster
    logging.info("Loading original inundation raster")
    with rasterio.open(original_inundation_path) as inund:
        inund_data = inund.read(1, masked=True)
        inund_transform = inund.transform
        inund_crs = inund.crs

        # Ensure CRS match
        if dem_crs != inund_crs:
            raise ValueError("CRS of DEM and Inundation raster do not match.")

        # Reclassify inundation raster
        logging.info("Reclassifying inundation raster")
        reclassified_inundation = np.where(inund_data > 0, 1, 0)

        # Save the reclassified inundation raster
        logging.info("Saving reclassified inundation raster")
        reclassified_profile = inund.profile
        reclassified_profile.update(dtype=rasterio.int32, count=1)
        with rasterio.open(reclassified_inundation_path, 'w', **reclassified_profile) as dst:
            dst.write(reclassified_inundation.astype(rasterio.int32), 1)

    # Reopen the DEM and reclassified inundation raster
    with rasterio.open(reclassified_inundation_path) as reclassified_inund:
        reclassified_inund_data = reclassified_inund.read(1, masked=True)
        reclassified_transform = reclassified_inund.transform

    # Resample DEM to match the resolution and extent of the inundation raster
    logging.info("Resampling DEM to match the resolution and extent of the inundation raster")
    dem_resampled = np.empty_like(reclassified_inund_data)
    rasterio.warp.reproject(
        source=dem_data,
        destination=dem_resampled,
        src_transform=dem_transform,
        src_crs=dem_crs,
        dst_transform=reclassified_transform,
        dst_crs=dem_crs,
        resampling=Resampling.nearest
    )

    # Initialize water depth array
    water_depth = np.zeros_like(dem_resampled, dtype=np.float32)

    # Calculate water depth where the inundation raster indicates flooding
    logging.info("Calculating water depth")
    water_depth = np.where(reclassified_inund_data == 1, dem_resampled - np.nanmin(dem_resampled[reclassified_inund_data == 1]), 0)

    # Apply a low-pass filter to smooth the water depth raster
    logging.info("Applying low-pass filter to smooth the water depth raster")
    water_depth_filtered = gaussian_filter(water_depth, sigma=1)

    # Save the water depth raster
    logging.info("Saving the water depth raster")
    output_profile = reclassified_profile
    output_profile.update(dtype=rasterio.float32, count=1, compress='lzw')

    with rasterio.open(WaterDepthOutput, 'w', **output_profile) as dst:
        dst.write(water_depth_filtered.astype(rasterio.float32), 1)

    logging.info("Water depth estimation process completed successfully")

except Exception as e:
    logging.error(f"An error occurred during the water depth estimation process: {e}")