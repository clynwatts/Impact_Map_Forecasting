import os
import json
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from shapely.geometry import box
from osgeo import gdal, ogr, osr

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

svi_folder = config['svi_folder']
gdb_path = os.path.join(svi_folder, 'SVI2022_TEXAS_tract.gdb')
area_shapefile = os.path.join(svi_folder, 'AOI', 'HUC8_Houston4326.shp')
svi_raster_path = os.path.join(svi_folder, 'SVI.tif')

# Check if SVI raster already exists
if os.path.exists(svi_raster_path):
    print("SVI raster already exists. Skipping creation.")
else:
    print("Creating SVI raster...")

    # Load the ESRI Geodatabase
    gdf = gpd.read_file(gdb_path)

    # Load the shapefile for your area
    area_gdf = gpd.read_file(area_shapefile)

    # Reproject the shapefile to match the CRS of the ESRI Geodatabase
    area_gdf = area_gdf.to_crs(gdf.crs)

    # Clip the geodatabase data to your area
    clipped_gdf = gpd.clip(gdf, area_gdf)

    # Save the clipped data for further processing
    clipped_gdf.to_file(os.path.join(svi_folder, 'clipped_data_SVI.shp'))

    # Load the clipped data
    clipped_gdf = gpd.read_file(os.path.join(svi_folder, 'clipped_data_SVI.shp'))

    # Plot the clipped data
    fig, ax = plt.subplots(figsize=(10, 10))
    clipped_gdf.plot(ax=ax, edgecolor='k')
    plt.title('SVI Data Houston city')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.show()

    # Identify the columns starting with 'F_'
    flag_columns = [col for col in clipped_gdf.columns if col.startswith('F_')]

    # Keep geospatial columns (geometry) and flag columns
    columns_to_keep = ['geometry'] + flag_columns
    clipped_gdf = clipped_gdf[columns_to_keep]

    # Function to fill -999 values with the average of neighboring values
    def fill_missing_values(gdf, columns):
        for col in columns:
            missing_indices = gdf[gdf[col] == -999].index
            for idx in missing_indices:
                neighbors = gdf[gdf.geometry.touches(gdf.loc[idx, 'geometry'])]
                if not neighbors.empty:
                    gdf.at[idx, col] = int(np.round(neighbors[col].replace(-999, np.nan).mean()))
        return gdf

    # Fill missing values
    clipped_gdf = fill_missing_values(clipped_gdf, flag_columns)

    # Save the cleaned data
    clipped_gdf.to_file(os.path.join(svi_folder, 'cleaned_data_SVI.shp'))

    # Load the cleaned data
    clipped_gdf = gpd.read_file(os.path.join(svi_folder, 'cleaned_data_SVI.shp'))

    # Select specific variables for SVI calculation
    selected_variables = ['F_POV150', 'F_UNEMP', 'F_HBURD', 'F_UNINSUR', 'F_AGE65', 'F_AGE17', 'F_DISABL', 'F_LIMENG', 'F_MUNIT', 'F_MOBILE', 'F_CROWD', 'F_NOVEH', 'F_GROUPQ']
    clipped_gdf['SVI'] = clipped_gdf[selected_variables].sum(axis=1) + 1  # Add one to the SVI values

    # Remove all columns except 'geometry' and 'SVI'
    clipped_gdf = clipped_gdf[['geometry', 'SVI']]

    # Visualize the SVI with a legend
    fig, ax = plt.subplots(figsize=(10, 10))
    num_classes = int(clipped_gdf['SVI'].max())
    cmap = plt.cm.viridis
    norm = colors.BoundaryNorm(np.linspace(clipped_gdf['SVI'].min(), clipped_gdf['SVI'].max(), num_classes + 1), cmap.N)
    clipped_gdf.plot(column='SVI', cmap=cmap, linewidth=0.8, ax=ax, edgecolor='0.8', legend=False, norm=norm)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []
    cbar = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.01)
    cbar.set_label('SVI')
    plt.title('Social Vulnerability Index (SVI)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.show()

    # Save the SVI data
    clipped_gdf.to_file(os.path.join(svi_folder, 'svi_data_nonad_0810.shp'))

    # Rasterize the SVI shapefile
    shapefile_path = os.path.join(svi_folder, 'svi_data_nonad_0810.shp')
    input_shp = ogr.Open(shapefile_path)
    source_layer = input_shp.GetLayer()
    xmin, xmax, ymin, ymax = source_layer.GetExtent()
    pixel_size = 0.0001
    x_res = int(round((xmax - xmin) / pixel_size))
    y_res = int(round((ymax - ymin) / pixel_size))
    target_ds = gdal.GetDriverByName('GTiff').Create(svi_raster_path, x_res, y_res, 1, gdal.GDT_Float32, ['COMPRESS=LZW'])
    target_ds.SetGeoTransform((xmin, pixel_size, 0, ymax, 0, -pixel_size))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4269)  # EPSG:4269 is NAD83
    target_ds.SetProjection(srs.ExportToWkt())
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(-9999)
    band.Fill(-9999)
    gdal.RasterizeLayer(target_ds, [1], source_layer, options=['ALL_TOUCHED=TRUE', 'ATTRIBUTE=SVI'])
    target_ds = None

    print("Rasterization complete!")
