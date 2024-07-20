import os
import boto3
import pandas as pd
import subprocess
import json  
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError


# Function to set up AWS credentials
def setup_aws_credentials():
    os.environ['AWS_ACCESS_KEY_ID'] = 'AKIARNNK42TENXRKIBZU'
    os.environ['AWS_SECRET_ACCESS_KEY'] = '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'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Function to sync data from S3
def sync_data_from_s3(bucket_name, prefix, local_dir):
    try:
        sync_command = f"aws s3 sync s3://{bucket_name}/{prefix} {local_dir} --request-payer"
        result = subprocess.run(sync_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Successfully synced data from s3://{bucket_name}/{prefix} to {local_dir}")
        else:
            print(f"Error syncing data: {result.stderr}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to prepare feature ID CSV
def prepare_feature_id_csv(hydrotable_path, output_csv_path):
    if not os.path.exists(hydrotable_path):
        print(f"Error: {hydrotable_path} does not exist.")
        return

    hydrotable_df = pd.read_csv(hydrotable_path)
    unique_feature_ids = hydrotable_df['feature_id'].drop_duplicates()
    unique_feature_ids_df = pd.DataFrame(unique_feature_ids, columns=['feature_id'])
    unique_feature_ids_df.insert(0, '', range(len(unique_feature_ids_df)))
    unique_feature_ids_df.to_csv(output_csv_path, index=False)
    print('Row numbers added and CSV file saved successfully.')

# Main function to orchestrate the workflow
def main():
    # Load configuration
    config_path = r"D:/Hesham/test/config.json"
    with open(config_path) as config_file:
        config = json.load(config_file)

    HUC_ID = config['HUC_ID']
    local_dir = config['local_dir']
    bucket_name = config['bucket_name']
    prefix_base = config['prefix_base']
    output_csv_filename = config['output_csv_filename']
    prefix = f"{prefix_base}{HUC_ID}"
    output_csv_path = os.path.join(local_dir, output_csv_filename)
    
    # Set up AWS credentials
    setup_aws_credentials()
    
    # Paths
    hydrotable_path = os.path.join(local_dir, 'hydrotable.csv')

    # Check if feature_id CSV already exists
    if not os.path.exists(output_csv_path):
        print("Running initial setup...")
        
        # Sync data from S3
        sync_data_from_s3(bucket_name, prefix, local_dir)
        
        # Verify if hydrotable.csv exists
        if os.path.exists(hydrotable_path):
            print(f"{hydrotable_path} found.")
            # Prepare feature ID CSV
            prepare_feature_id_csv(hydrotable_path, output_csv_path)
        else:
            print(f"{hydrotable_path} does not exist after sync. Please check the S3 bucket and prefix.")
    else:
        print("Feature ID CSV already exists. Skipping initial setup.")

if __name__ == "__main__":
    main()