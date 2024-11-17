import math
from station_handling import *
from custom_warnings import *

# only keep certain columns that we care about, rename them
def clean_data(data):
    # only keep the below columns
    cols_to_keep = ["Date", "Color", "PM2.5_19 (ug/m3)", "PM2.5_20 (ug/m3)", "Station", "N/S", "Station"]
    data = data.drop(columns=list(filter(lambda col: col not in cols_to_keep, data.columns)))

    # rename
    data.rename(columns={'PM2.5_19 (ug/m3)': 'PM2_5_19', 'PM2.5_20 (ug/m3)': 'PM2_5_20', 'N/S': 'Direction'}, inplace=True)
    return data

# given a cleaned df containing minute-by-minute measurements, line color, and whether to skip faulty data from red line
# return three dictionarys (stations_PM, segments_PM, segment_Time)
# stations_PM will have stations as keys, a list of all PM measurements as the value
# segments_PM will have segments as keys, a list of all PM measurements as the value
# segments_Time will have segments as keys, a list of all the number of minutes on that segment for each trip (should be length 8)
def get_pm_and_time(cleaned_df, line_color, skip_red19_bad_data = False):
    stations_PM = {}
    segments_PM = {}
    segments_Time = {}

    if line_color == "red" and skip_red19_bad_data:
        custom_warn("ALERT: Skipping monitor 19's faulty 1s on the red line that are < 3 times that of monitor 20.")
    
    # probably better to have nested for in this if, rather than checking every line
    if line_color == "red":
        last_station = None
        between_station_buffer = []
        for row in cleaned_df.itertuples():
            station_name = row.Station
            if row.Direction == 'Southbound':  # keeping stations and segments

                # if were on the train
                if station_name == 'Between Stations':
                    # append
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20

                    # if skipping bad data and satisfies conditions as bad data, just append monitor 20's data
                    if skip_red19_bad_data and (PM2_5_19 == 1):
                        if not math.isnan(PM2_5_20):
                            between_station_buffer.append(PM2_5_20)
                    else:
                        if not math.isnan(PM2_5_19):
                            between_station_buffer.append(PM2_5_19)
                        if not math.isnan(PM2_5_20):
                            between_station_buffer.append(PM2_5_20)

                else:
                    # we hit a new station, add the buffer to segments_PM and segments_PM time
                    if (last_station is not None) and (last_station != station_name):
                        segment_name = get_adjacent_station_pair(station_name, last_station)

                        # catch dictionary doesnt have key case
                        if segment_name not in segments_PM:
                            segments_PM[segment_name] = []
                            segments_Time[segment_name] = []

                        # add the between station PM and Time data
                        segments_Time[segment_name].append(len(between_station_buffer)/2)
                        segments_PM[segment_name].extend([x for x in between_station_buffer if not math.isnan(x)])

                    # if station is in not dictionary, add it
                    if station_name not in stations_PM:
                        stations_PM[station_name] = []
                    
                    # get PM measurements
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20

                    # if skipping bad data and satisfies conditions as bad data, just append good data
                    if skip_red19_bad_data and (PM2_5_19 == 1):
                        if not math.isnan(PM2_5_20):
                            stations_PM[station_name].append(PM2_5_20)
                    else:
                        if not math.isnan(PM2_5_19):
                            stations_PM[station_name].append(PM2_5_19)
                        if not math.isnan(PM2_5_20):
                            stations_PM[station_name].append(PM2_5_20)

                    # set this station as the last station
                    last_station = station_name
                    between_station_buffer = []
                
            if row.Direction == 'Northbound':  # keeping segments
                
                # if were on the train
                if station_name == 'Between Stations':
                    # append
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20

                    # if skipping bad data and satisfies conditions as bad data, just append monitor 20's data
                    if skip_red19_bad_data and (PM2_5_19 == 1):
                        between_station_buffer.append(row.PM2_5_20)
                    else:
                        between_station_buffer.append(row.PM2_5_19)
                        between_station_buffer.append(row.PM2_5_20)

                else:
                    # we hit a new station, add the buffer to segments_PM and segments_PM time
                    if (last_station is not None) and (last_station != station_name):
                        segment_name = get_adjacent_station_pair(station_name, last_station)

                        # catch dictionary doesnt have key case
                        if segment_name not in segments_PM:
                            segments_PM[segment_name] = []
                            segments_Time[segment_name] = []

                        # add the between station PM and Time data
                        segments_Time[segment_name].append(len(between_station_buffer)/2)
                        segments_PM[segment_name].extend([x for x in between_station_buffer if not math.isnan(x)])

                    # set this station as the last station
                    last_station = station_name
                    between_station_buffer = []

    else:  # yellow line
        last_station = None
        between_station_buffer = []
        for row in cleaned_df.itertuples():
            station_name = row.Station
            if row.Direction == 'Southbound':  # keeping  segments

                # if were on the train
                if station_name == 'Between Stations':
                    # append
                    between_station_buffer.append(row.PM2_5_19)
                    between_station_buffer.append(row.PM2_5_20)

                else:
                    # we hit a new station, add the buffer to segments_PM and segments_PM time
                    if (last_station is not None) and (last_station != station_name):
                        segment_name = get_adjacent_station_pair(station_name, last_station)

                        # catch dictionary doesnt have key case
                        if segment_name not in segments_PM:
                            segments_PM[segment_name] = []
                            segments_Time[segment_name] = []

                        # add the between station PM and Time data
                        segments_Time[segment_name].append(len(between_station_buffer)/2)
                        segments_PM[segment_name].extend([x for x in between_station_buffer if not math.isnan(x)])

                    # set this station as the last station
                    last_station = station_name
                    between_station_buffer = []
                
            if row.Direction == 'Northbound':  # keeping segments and stations

                # if were on the train
                if station_name == 'Between Stations':
                    # append
                    between_station_buffer.append(row.PM2_5_19)
                    between_station_buffer.append(row.PM2_5_20)

                else:
                    # we hit a new station, add the buffer to segments_PM and segments_PM time
                    if (last_station is not None) and (last_station != station_name):
                        segment_name = get_adjacent_station_pair(station_name, last_station)

                        # catch dictionary doesnt have key case
                        if segment_name not in segments_PM:
                            segments_PM[segment_name] = []
                            segments_Time[segment_name] = []

                        # add the between station PM and Time data
                        segments_Time[segment_name].append(len(between_station_buffer)/2)
                        segments_PM[segment_name].extend([x for x in between_station_buffer if not math.isnan(x)])

                    # if station is in dictionary, add it
                    if station_name not in stations_PM:
                        stations_PM[station_name] = []
                    
                    # get PM measurements
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20
                    # only append if measurement is a number
                    if not math.isnan(PM2_5_19):
                        stations_PM[station_name].append(PM2_5_19)
                    if not math.isnan(PM2_5_20):
                        stations_PM[station_name].append(PM2_5_20)

                    # set this station as the last station
                    last_station = station_name
                    between_station_buffer = []     

    return (stations_PM, segments_PM, segments_Time)