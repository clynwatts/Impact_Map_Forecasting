import subprocess
import os
import json
import sys
import netCDF4 as nc

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

HUC_ID = config['HUC_ID']
local_dir = config['local_dir']
output_csv_filename = config['output_csv_filename']
prepare_feature_ids_script = config['prepare_feature_ids_script']
streamflow_processing_script = config['streamflow_processing_script']
hand_fim_generation_script = config['hand_fim_generation_script']
create_impact_map_script = config['create_impact_map_script']
publish_arcgis_online_script = config['publish_arcgis_online_script']

def run_script(script_path):
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Error running script {script_path}: {result.stderr}")

try:
    # Check if feature_id CSV already exists
    feature_id_csv_path = os.path.join(local_dir, output_csv_filename)
    if not os.path.exists(feature_id_csv_path):
        print("Running the initial setup script...")
        run_script(prepare_feature_ids_script)
    else:
        print("Feature ID CSV already exists. Skipping initial setup.")

    # Run the streamflow processing script
    print("Running the streamflow processing script...")
    run_script(streamflow_processing_script)

    # Run the HAND-FIM generation script
    print("Running the HAND-FIM generation script...")
    run_script(hand_fim_generation_script)
    print("HAND-FIM generation completed successfully.")

    # Run the create impact map script
    print("Running the create impact map script...")
    run_script(create_impact_map_script)
    print("Impact map generation completed successfully.")

    # Run the publish to ArcGIS Online script
    print("Running the publish to ArcGIS Online script...")
    run_script(publish_arcgis_online_script)
    print("Publishing to ArcGIS Online completed successfully.")

except RuntimeError as e:
    print(f"Process failed: {e}")
    sys.exit(1)