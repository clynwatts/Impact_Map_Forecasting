# Operational Workflow for Flood Impact Forecast (Generation and Automation)

## Overview
This project involves generating an impact map based on streamflow and SVI data, processing the data, and uploading the results to ArcGIS Online. The workflow includes downloading necessary data, processing it to create an impact map, and automating the upload of the map to ArcGIS Online.

## Requirements
- ArcGIS Online Account
- Python 3.9
- Necessary Python packages listed in `requirements.yml`

## Configuration
Ensure that you have a `config.json` file in your project directory with the following structure:
```json
{
  "HUC_ID": "12040104",
  "local_dir": "D:/Hesham/test/12040104",
  "download_dir": "D:/Hesham/test/download",
  "bucket_name": "noaa-nws-owp-fim",
  "prefix_base": "hand_fim/fim_4_4_0_0/",
  "output_csv_filename": "12040104_feature_id.csv",
  "repository_path": "D:/Hesham/test/HAND-FIM/inundation-mapping",
  "hand_fim_repo_url": "https://github.com/NOAA-OWP/inundation-mapping.git",
  "env_file_path": "D:/Hesham/test/HAND-FIM/inundation-mapping/.env",
  "output_path": "D:/Hesham/test/HAND-FIM/output",
  "fim_temp_path": "D:/Hesham/test/HAND-FIM/Outputs_temp",
  "data_path": "D:/Hesham/test/download/",
  "huc_folder_path": "D:/Hesham/test/12040104",
  "branch_ids_file": "D:/Hesham/test/12040104/branch_ids.csv",
  "fim_inputs_file": "D:/Hesham/test/HAND-FIM/output/fim_inputs.csv",
  "prepare_feature_ids_script": "D:/Hesham/test/scripts/prepare_feature_ids.py",
  "streamflow_processing_script": "D:/Hesham/test/scripts/download_streamflow_andprocessing.py",
  "hand_fim_generation_script": "D:/Hesham/test/scripts/hand_fim_generation.py",
  "svi_folder": "D:/Hesham/test/SVI",
  "impact_folder": "D:/Hesham/test/Impact_map/output",
  "create_impact_map_script": "D:/Hesham/test/scripts/Create_impact_map_1.py",
  "publish_arcgis_online_script": "D:/Hesham/test/scripts/Publish_ArcGIS_Online.py"
}
```

1- Setup
```
git clone https://github.com/your_username/your_repo.git
cd your_repo
```
2- Set up Python environment:
```
conda env create -f requirements.yml
conda activate impact_map_env
```

3- Manually set ArcGIS credentials (inside "Publish_ArcGIS_Online")
```
username = "your_username"
password = "your_password"

```
## Running the Scripts
### 1-Initial Setup:
Ensure the `prepare_feature_ids.py` script is configured and run it to prepare initial data. This script is responsible for preparing the initial feature IDs needed to extract streamflow data. Here you will need to define your HUC_ID to get the feature_ids in your HUC.


### 2-Streamflow Processing:
Run the `streamflow_processing.py` script to download and process streamflow data. The script is designed to download the 18 hours forecasts streamflow form the National Water Model every hour. The old data will be flushed evey hour. The script calulate the maximum discharge of each feature id within the 18 hours. The final output for this step is a CSV file contains max discharge value of the 18 hours.  
```
python streamflow_processing.py
```

### 3- HAND-FIM Generation:
Generate HAND-FIM maps by running the respective script (No Docker needed). The HAND-FIM takes the last CSV file as input to generate both Inundation map and Flood depth map. 
```
python hand_fim_generation.py
```

### 4- Create SVI map
Set this `Create_SVI_raster` script only one time. Also, this is not included in the main .py file as it needs to run one time, so, You should run it separately. 

### 5- Create Impact Map:
Create the impact map using the prepared data. This script mainly depending on multiplying the SVI raster BY the Depth map. 
```
python Create_impact_map.py
```
### 6- Publish to ArcGIS Online:
Upload the impact map to ArcGIS Online and update the web map. Creating and Configuring ArcGIS Online Components has to be set-up for one time outside the script (on ArcGIS Online)
    1- Create a Hosted Feature Layer and add the zipped reclassified impact map from last step
    2- Connect the Layer to a Web Map
    3- Create an Instant App and link
After you set-up the ArcGIS online configuring, RUN the script. 
```
python publish_arcgis_online.py
```
You can check our ArcGIS Instant App using the following link: 
[Impact-based Flood Forcast App](https://wmugeography.maps.arcgis.com/apps/instant/atlas/index.html?appid=2088172c05fc45269099be65f233b37f)
Open the Map and Add the 'Flood Impact Forecast'


### 7- Tasker Scheduler 
Scheduling the Workflow
To schedule the workflow to run hourly on Windows:
1.	Open Task Scheduler.
2.	Create a new task.
3.	Set the trigger to repeat every hour.
4.	Set the action to run `18_hour_flood_impact_forecast.py` using the Python interpreter from the Conda environment.
5. Please make sure when you Set the Action, Select "Start a program":
In the "Program/script" field, enter the path to the Python executable (with the environment)
   ```
   c:\Users\hhp1483\AppData\Local\anaconda3\envs\py310\python.exe
   ```
In the "Add arguments" field, enter the path to 18_hour_flood_impact_forecast.py
  
## Notes
### HAND-FIM notebook
It can run without Docker. this notebook is not related the workflow. 

### Forecast Confidence notebook (Not Fully Automated) 
This process was tested on the hourly basis forecast, and it was not included in the workflow. A flood forecast confidence map indicates the reliability of flood predictions, showing the likelihood of an area being flooded. It is important because it helps decision-makers assess the certainty of flood forecasts, improving preparedness and response strategies. To create the flood forecast confidence map using the Flood Inundation Maps (FIMs), we followed the process outlined in figure 2. Every hour, the NWM provides a forecast for each of the next 18 hours. This means that a single hour will be forecasted 18 times, at each of the previous hours. Within the 18 iterations, the single-hour forecast suffers from inconsistency, where some iterations predict widespread flooding and other iterations predict little. For example, a forecast published at 7:00 am (real time) for 5:00 pm shows a specific area as flooded, but the same forecast for 5:00 pm at 8:00 am (real-time) shows the same area as non-flooded. This inconsistency poses a challenge for decision-makers, watching flood predictions change from hour to hour. To address this inconsistency, we calculated the hourly flood forecast confidence based on the previous forecasts, to produce a forecast confidence map.  
For more infoemation about this process please check our Report: http//... 

### SVI DATA  
Dowonload the ESRI Geodatabase data in census tract level using the link >>> [Data Source](https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html)

[Documentation](https://www.atsdr.cdc.gov/placeandhealth/svi/documentation/pdf/SVI-2022-Documentation-H.pdf)


### Results
There is `test folder` contains all the inputs and the outputs of the 18 hours forecast operational process. It can be used as a test to be familiar with the workflow. You can download it using the following link: https://drive.google.com/file/d/1wRT-Asijo6HPSTmUeuPWgG9o3zGCUu_z/view?usp=sharing

for more information about this work please check our report using the following Link:  http/...

### Contributing
We welcome contributions from the community. Please follow these steps to contribute:
1.	Fork the repository.
2.	Create a new branch (git checkout -b feature-branch).
3.	Commit your changes (git commit -m 'Add new feature').
4.	Push to the branch (git push origin feature-branch).
5.	Open a pull request.

### License
This project is licensed under the MIT License. See the LICENSE file for details.
________________________________________
This README provides a comprehensive overview of your project and guides users on how to use it effectively. Adjust the file paths, script names, and repository URL as needed.
