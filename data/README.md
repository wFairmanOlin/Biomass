# Data

The biomass sensor system collects and stores data from the sensors in a central **Firebase** server. A subset of that data can be found in [`latest_data.json`](latest_data.json). 

In addition to sensor data, technicians at HBOI manually record algae density on a reguar interval. The manually collected information is found in [`harvest_log.csv`]. 

If a sensor is temporarily removed for maintenance, switched to another tank, or experiences an anomaly, the event will be recorded in [`sensor_log.csv`]

Please explore ['process_data.ipynb`](process_data.ipynb) notebook to explore the data.

## Old Data

Before developing the current sensor, we manually collected data from our first generation sensor for a two month period. The data from this sensor is found in [old_sensor](old_sensor/).

### Naming Scheme of Folders
The folders are labeled as follows. The hours are in military time (0 to 23) instead of am/pm.

```
<Start Date (DD)>_to_<End Date (DD)>_start_<Start Time (HH_MM)>_end_<End Time (HH_MM)> 
```

### Data Processing

Example code for processing and plotting the raw data collected by the sensors is found in the jupyter notebook [process_data_old.ipynb](/old_sensor/process_data.ipynb).

The data is collected in two [complementary golay squences](https://en.wikipedia.org/wiki/Complementary_sequences). For each timestamp, 64 measurements are made by the sensor. The processing code reduces the 64 measurements into a single measurement that should be robust to external noise. In each folder, the raw data can be found in the `GOLAYSEQ.CSV` file. 

Extra sensor information like battery voltage can be found in the `LOG.CSV` file.
