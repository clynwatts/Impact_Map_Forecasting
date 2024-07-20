import subprocess
import os
import sys
import shutil
import pandas as pd
from dotenv import load_dotenv
import json

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

HUC_ID = config['HUC_ID']
local_dir = config['local_dir']
max_discharge_file = os.path.join(config['download_dir'], "discharge.csv")
repository_path = config['repository_path']

# Clone the repository if it doesn't exist
if not os.path.exists(repository_path):
    subprocess.run(["git", "clone", config['hand_fim_repo_url'], repository_path])
else:
    print("Repository already exists. Skipping clone.")

# Set up paths
tools_path = os.path.join(repository_path, "tools")
src_path = os.path.join(repository_path, "src")
output_path = config['output_path']
fim_temp_path = config['fim_temp_path']
huc_folder_path = config['huc_folder_path']
output_huc_folder_path = os.path.join(output_path, HUC_ID)
branch_ids_file = config['branch_ids_file']
fim_inputs_file = config['fim_inputs_file']

# Ensure all necessary directories exist
os.makedirs(output_path, exist_ok=True)
os.makedirs(fim_temp_path, exist_ok=True)
os.makedirs(huc_folder_path, exist_ok=True)
os.makedirs(output_huc_folder_path, exist_ok=True)

# Step 1: Copy the entire HUC folder to the output directory
if os.path.exists(output_huc_folder_path):
    shutil.rmtree(output_huc_folder_path)  # Remove the existing folder if it exists
shutil.copytree(huc_folder_path, output_huc_folder_path)
print(f"Copied {huc_folder_path} to {output_huc_folder_path}")

# Step 2: Copy branch_ids.csv to the output folder, keep only the first row, and rename it to fim_inputs.csv
if os.path.exists(branch_ids_file):
    df = pd.read_csv(branch_ids_file)
    df_first_row = df.iloc[:0]
    df_first_row.to_csv(fim_inputs_file, index=False)
    print(f"Copied first row of {branch_ids_file} to {fim_inputs_file}")
else:
    print(f"{branch_ids_file} does not exist")

# Create the .env file and write the environment variables
env_content = f"""
inputsDir={local_dir}/HAND-FIM/inputs
outputsDir={local_dir}/HAND-FIM/output
"""

env_file_path = config['env_file_path']

with open(env_file_path, "w") as f:
    f.write(env_content)

print(f".env file created at {env_file_path} with content:\n{env_content}")

# Load environment variables from .env file
dotenv_path = env_file_path
load_dotenv(dotenv_path)

# Verify that the environment variables are loaded
inputs_dir = os.getenv('inputsDir')
outputs_dir = os.getenv('outputsDir')
print(f"inputsDir: {inputs_dir}")
print(f"outputsDir: {outputs_dir}")

# Add src and repository_path to the Python path
sys.path.append(src_path)
sys.path.append(repository_path)

# Process the max discharge file to generate FIMs
csv_file_path = max_discharge_file
base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
inundation_output_file = os.path.join(output_path, f'i_{base_name}.tif')
depth_output_file = os.path.join(output_path, f'd_{base_name}.tif')

# Define the command to run the inundation script
command_to_run = [
    sys.executable,
    os.path.join(tools_path, "inundate_mosaic_wrapper.py"),
    "-y", output_path,
    "-u", HUC_ID,
    "-f", csv_file_path,
    "-i", inundation_output_file,
    "-d", depth_output_file
]

# Run the command with the correct working directory and PYTHONPATH
env = os.environ.copy()
env['PYTHONPATH'] = f"{src_path}{os.pathsep}{repository_path}"

result = subprocess.run(command_to_run, cwd=tools_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Print the output and error (if any)
print("Subprocess stdout output:")
print(result.stdout.decode())

print("Subprocess stderr output:")
print(result.stderr.decode())

# Check if the command was successful
if result.returncode == 0:
    print(f"Inundation mapping completed successfully for {csv_file_path}")
else:
    print(f"Failed to complete inundation mapping for {csv_file_path}")
    # Additional troubleshooting suggestions
    print("Possible issues:")
    print("- Check if the input CSV file format is correct.")
    print("- Ensure the environment variables are set correctly.")
    print("- Verify the inundate_mosaic_wrapper.py script is working as expected.")
    print("- Check for any missing dependencies or permissions issues.")
