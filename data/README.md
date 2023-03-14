This folder contains samples of both raw data collected directly from the biomass sensors as well as processed data. This folder does not and should not contain all of the data collected by the biomass sensor system. Instead, this folder currently contains just the data collected manually. All of our data will eventually be available in our **Firebase database**.

## Data Collection

The data collected manually is recorded in periods lasting anywhere from 24 hours to several days. Each folder is named according to when the data collection started and finished. Inside each folder is a `info.md` that provides some information about the data collected: tank id, sensor version, sensor orientation, and location of the sensor inside the tank. 

There are currently six algae tanks in operation. There is a possibility of two different algae species in each tank, however, we are not currently tracking which tank has which species. 

![tank layout](tank_layout.png)

We have developed two different sensors for data collection. Both versions use the same laser and photodiode receiver. This should make results from both versions nearly identical but we are still tracking which data has been collected from which version. The first version can be mounted in any location near the surface of the water. The orientation can also change between facing the bottom of the tank or facing the side of the tank. The second version can only be mounted to the walls of the tank. This version is also always oriented horizontally, facing the opposite wall.

### Naming Scheme of Folders
The folders are labeled as follows. The hours are in military time (0 to 23) instead of am/pm.

```
<Start Date (DD)>_to_<End Date (DD)>_start_<Start Time (HH_MM)>_end_<End Time (HH_MM)> 
```

## Data Processing

Example code for processing and plotting the raw data collected by the sensors is found in the jupyter notebook [process_data](process_data.ipynb).

The data is collected in two [complementary golay squences](https://en.wikipedia.org/wiki/Complementary_sequences). For each timestamp, 64 measurements are made by the sensor. The processing code reduces the 64 measurements into a single measurement that should be robust to external noise. In each folder, the raw data can be found in the `GOLAYSEQ.CSV` file. 

Extra sensor information like battery voltage can be found in the `LOG.CSV` file.

##  Data Validation

The sensors are taking measurements every few minutes. The true density values for each tank, however, are recorded on a weekly to monthly basis. When available, these values will be available in a CSV file. 

