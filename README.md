# Impact_Map_Forecasting

The flood impact map: calculates the impact of a given flood prediction on different censuc tracts, based on the CDC SVI

Import 18hr highflow forecast: downloads stream discharge forecast published by NOAA and updated every hour. The script can be modified to download 12hr, 24hr forecasts as well. It modifies the data into a table that can be read by handfim

OWP HANDFIM: Runs handfim. and outputs a fim with depth values

forecast_input csv file: a sample output from the import 18hr forecast

Query_store_Forecast: queries and downloads forecast data and saves it as a shapefile

5day_forecast: runfile to automate the output of Impact maps from forecast data

FwDET2.1: calculates depth from inundation extent
