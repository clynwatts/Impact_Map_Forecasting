import os
import zipfile
import logging
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Manually set ArcGIS credentials
username = "USERNAME"
password = "PASSWORD"

# Paths and parameters
shapefile_folder = r"D:/Hesham/test/Impact_map/output"
shapefile_zip_path = os.path.join(shapefile_folder, "impact_map_shapefile.zip")
hosted_feature_layer_id = "ed168c42dc184134a95dbe9b9fb5f554"  # Replace with your actual hosted feature layer ID

def zip_shapefile(shapefile_folder, shapefile_zip_path):
    with zipfile.ZipFile(shapefile_zip_path, 'w') as zipf:
        for root, _, files in os.walk(shapefile_folder):
            for file in files:
                if file.endswith(('.shp', '.shx', '.dbf', '.prj', '.cpg')):
                    zipf.write(os.path.join(root, file), arcname=file)

def update_feature_layer(gis, shapefile_zip_path, hosted_feature_layer_id):
    try:
        # Access the existing hosted feature layer
        feature_layer_item = gis.content.get(hosted_feature_layer_id)
        if feature_layer_item is None:
            raise ValueError(f"Hosted Feature Layer with ID {hosted_feature_layer_id} not found")

        # Get the FeatureLayerCollection
        feature_layer_collection = FeatureLayerCollection.fromitem(feature_layer_item)
        feature_layer = feature_layer_collection.layers[0]

        # Delete existing features
        logging.info("Deleting existing features from the hosted feature layer")
        feature_layer.delete_features(where="1=1")

        # Overwrite the feature layer with the new shapefile
        logging.info("Overwriting the hosted feature layer with the new shapefile")
        feature_layer_collection.manager.overwrite(shapefile_zip_path)
        logging.info("Hosted feature layer updated successfully")
    except Exception as e:
        logging.error(f"An error occurred while updating the feature layer: {e}")

try:
    # Step 1: Zip the shapefile
    logging.info("Zipping the shapefile")
    zip_shapefile(shapefile_folder, shapefile_zip_path)
    logging.info("Shapefile zipped successfully")

    # Step 2: Initialize GIS and update the hosted feature layer
    logging.info("Updating the hosted feature layer")
    gis = GIS("https://www.arcgis.com", username, password)
    update_feature_layer(gis, shapefile_zip_path, hosted_feature_layer_id)
    logging.info("Hosted feature layer updated successfully")

except Exception as e:
    logging.error(f"An error occurred: {e}")