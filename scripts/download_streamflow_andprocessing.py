import os
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import netCDF4 as nc
import pandas as pd
import shutil

# Load configuration
config_path = r"D:/Hesham/test/config.json"
with open(config_path) as config_file:
    config = json.load(config_file)

url_base = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/"
output_dir = config['local_dir']
download_dir = config['download_dir']
output_csv_filename = config['output_csv_filename']

def clear_download_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def download_nc_files(date_str, current_hour):
    url = f"{url_base}/nwm.{date_str}/short_range/"
    date_output_dir = os.path.join(download_dir, date_str)
    os.makedirs(date_output_dir, exist_ok=True)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    pattern = re.compile(rf'nwm\.t{current_hour:02d}z\.short_range\.channel_rt\.f\d{{3}}\.conus\.nc')
    nc_files = [link['href'] for link in soup.find_all('a', href=True) if pattern.search(link['href'])]

    if not nc_files:
        return False, date_output_dir

    hour_output_dir = os.path.join(date_output_dir, f'{current_hour:02d}')
    os.makedirs(hour_output_dir, exist_ok=True)

    for nc_file in nc_files:
        file_url = url + nc_file
        file_path = os.path.join(hour_output_dir, nc_file)
        
        print(f'Downloading {file_url} to {file_path}')
        file_response = requests.get(file_url)
        with open(file_path, 'wb') as f:
            f.write(file_response.content)
        print(f'Download completed for {file_path}')

    print('All downloads completed for the date:', date_str)
    return True, hour_output_dir

def process_netcdf_file(netcdf_file_path, filter_df, output_folder_path):
    base_filename = os.path.basename(netcdf_file_path).replace('.nc', '')
    output_csv_file_path = os.path.join(output_folder_path, f'{base_filename}.csv')

    try:
        ds = nc.Dataset(netcdf_file_path, 'r')
        streamflow_data = ds.variables['streamflow'][:]
        feature_ids = ds.variables['feature_id'][:]
        ds.close()
    except Exception as e:
        print(f"Error reading NetCDF file {netcdf_file_path}: {e}")
        return

    if len(streamflow_data) == 0 or len(feature_ids) == 0:
        print(f"No data found in {netcdf_file_path}")
        return

    data_df = pd.DataFrame({
        'feature_id': feature_ids,
        'discharge': streamflow_data
    })

    filtered_df = data_df[data_df['feature_id'].isin(filter_df['feature_id'])]
    merged_df = pd.merge(filter_df[['feature_id']], filtered_df, on='feature_id')
    merged_df.to_csv(output_csv_file_path, index=False)
    print(f'Filtered DataFrame saved to {output_csv_file_path}')

def main():
    # Clear download directory before downloading new files
    clear_download_directory(download_dir)

    today = datetime.utcnow().strftime('%Y%m%d')
    current_hour = datetime.utcnow().hour

    success = False
    attempts = 0

    while not success and attempts < 24:
        attempts += 1
        success, date_output_dir = download_nc_files(today, current_hour)
        if not success:
            current_hour = (current_hour - 1) % 24
            if current_hour == 23:
                today = (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d')

    if not success:
        print("No recent forecast data found. Exiting.")
        return
    
    filter_csv_file_path = os.path.join(output_dir, output_csv_filename)
    output_folder_path = os.path.join(download_dir, "Data")
    os.makedirs(output_folder_path, exist_ok=True)

    filter_df = pd.read_csv(filter_csv_file_path)

    if os.path.exists(date_output_dir):
        for root, _, files in os.walk(date_output_dir):
            for filename in files:
                if filename.endswith('.nc'):
                    netcdf_file_path = os.path.join(root, filename)
                    process_netcdf_file(netcdf_file_path, filter_df, output_folder_path)
    
    csv_directory = output_folder_path
    csv_files = [file for file in os.listdir(csv_directory) if file.endswith('.csv')]

    if not csv_files:
        print("No CSV files found after processing NetCDF files.")
        return

    combined_df = pd.concat([pd.read_csv(os.path.join(csv_directory, file))[['feature_id', 'discharge']] for file in csv_files])

    combined_df = combined_df.pivot_table(index='feature_id', values='discharge', aggfunc=list).apply(pd.Series.explode).reset_index()
    combined_df['discharge'] = combined_df['discharge'].astype(float)
    combined_df = combined_df.groupby('feature_id')['discharge'].apply(list).reset_index()
    for i in range(1, len(combined_df['discharge'][0]) + 1):
        combined_df[f'discharge_{i}'] = combined_df['discharge'].apply(lambda x: x[i-1] if i-1 < len(x) else None)
    combined_df.drop(columns=['discharge'], inplace=True)

    output_file = os.path.join(download_dir, "combined_streamflow.csv")
    combined_df.to_csv(output_file, index=False)

    # Extract maximum discharge for each feature_id
    max_discharge_df = combined_df.set_index('feature_id').max(axis=1).reset_index()
    max_discharge_df.columns = ['feature_id', 'discharge']

    max_output_file = os.path.join(download_dir, "discharge.csv")
    max_discharge_df.to_csv(max_output_file, index=False)

    print(f'Maximum discharge values saved to {max_output_file}')

if __name__ == "__main__":
    main()
