from numpy.random import default_rng
import math
import numpy as np
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fitter import Fitter
from collections import deque
import warnings

# List of adjacent stations as pairs (Uptown-Downtown) for both red and yellow lines
adjacent_stations = [
    # Red Line (or others if specified)
    ("Downtown Berkeley", "Ashby"),
    ("Ashby", "MacArthur"),
    ("MacArthur", "19th St Oakland"),
    ("19th St Oakland", "12th St Oakland"),
    ("12th St Oakland", "West Oakland"),
    ("West Oakland", "Embarcadero"),
    ("Embarcadero", "Montgomery St"),
    ("Montgomery St", "Powell St"),
    ("Powell St", "Civic Center/UN Plaza"),
    ("Civic Center/UN Plaza", "16th St Mission"),
    ("16th St Mission", "24th St Mission"),

    # Yellow Line (or others if specified)
    ("Antioch", "Pittsburg Center"),
    ("Pittsburg Center", "Transfer Stop"),
    ("Transfer Stop", "Pittsburg/Bay Point"),
    ("Pittsburg/Bay Point", "North Concord/Martinez"),
    ("North Concord/Martinez", "Concord"),
    ("Concord", "Pleasant Hill/Contra Costa Centre"),
    ("Pleasant Hill/Contra Costa Center", "Walnut Creek"),
    ("Walnut Creek", "Lafayette"),
    ("Lafayette", "Orinda"),
    ("Orinda", "Rockridge"),
    ("Rockridge", "MacArthur")
]

# Accepts file_paths, holding 2 red and 2 yellow paths in that order
# returns list of (combined red, combined yellow) dataframes
def load_csv(file_paths):
    dfs = []
    for path in file_paths:
        try:
            dfs.append(pd.read_csv(path, skiprows=1))
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    red_combined_df = pd.concat(dfs[:2], axis=0, ignore_index=True)
    yellow_combined_df = pd.concat(dfs[2:], axis=0, ignore_index=True)

    return (red_combined_df, yellow_combined_df)

def clean_data(data):
    # only keep the below columns
    cols_to_keep = ["Date", "Color", "PM2.5_19 (ug/m3)", "PM2.5_20 (ug/m3)", "Station", "N/S", "Station"]
    data = data.drop(columns=list(filter(lambda col: col not in cols_to_keep, data.columns)))

    # rename
    data.rename(columns={'PM2.5_19 (ug/m3)': 'PM2_5_19', 'PM2.5_20 (ug/m3)': 'PM2_5_20', 'N/S': 'Direction'}, inplace=True)
    return data

def save_data(data):
    # Prompt user to enter the output file path
    output_path = input("Enter the path to save the cleaned CSV file (e.g., output.csv): ")
    try:
        data.to_csv(output_path, index=False)
        print(f"Data saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving the file: {e}")
    
def plot_list_of_distributions(list_of_distributions = None, list_of_distribution_names = None, name_x_y = ("Multiple Normal Distributions", 'Value', 'Density')):
    if list_of_distributions is None: 
        return None
    
    plt.figure(figsize=(10, 6))
    for i, distribution in enumerate(list_of_distributions):
        num_colors = len(list_of_distribution_names)
        colors = [plt.cm.rainbow(i / num_colors) for i in range(num_colors)]
        if list_of_distribution_names is not None:
            sns.kdeplot(distribution, label=list_of_distribution_names[i], color=colors[i])
        else:
            sns.kdeplot(distribution, label=f"Distribution {i + 1}", color=colors[i])
    
    plt.xlabel(name_x_y[1])
    plt.ylabel(name_x_y[2])
    plt.legend()
    plt.title(name_x_y[0])
    plt.show()


# given some a list of (lists of data points) and num_points
# returns a list of distributed points, each of len num_points
# distribution is normal
def list_of_distributions_generator(data_points_list=None, num_points=1000):
    if (data_points_list is None): 
        return None

    generated_distributions = []

    for i, data_points in enumerate(data_points_list):
        mean = np.mean(data_points)
        std_dev = np.std(data_points)

        # Generate normal distribution
        normal_dist = np.random.normal(mean, std_dev, num_points)
        generated_distributions.append(normal_dist)

    return generated_distributions

# given a cleaned df containing minute-by-minute measurements, line color, and whether to skip faulty data from red line
# return three dictionarys (stations_PM, segments_PM, segment_Time)
# stations_PM will have stations as keys, a list of all PM measurements as the value
# segments_PM will have segments as keys, a list of all PM measurements as the value
# segments_Time will have segments as keys, a list of all the number of minutes on that segment for each trip (should be length 8)
def get_pm_and_time(cleaned_df, line_color, skip_red19_bad_data = False):
    stations_PM = {}
    segments_PM = {}
    segments_Time = {}
    
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
                    if skip_red19_bad_data and (PM2_5_19 == 1) and (PM2_5_19 < 3*PM2_5_20):
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
                
            if row.Direction == 'Northbound':  # keeping segments
                
                # if were on the train
                if station_name == 'Between Stations':
                    # append
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20

                    # if skipping bad data and satisfies conditions as bad data, just append monitor 20's data
                    if skip_red19_bad_data and (PM2_5_19 == 1) and (PM2_5_19 < 3*PM2_5_20):
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

# copied straight from chatGPT
def get_adjacent_station_pair(station1, station2):
    """
    Given two station names, checks if they are adjacent (for both red and yellow line stations)
    and returns the standardized "UptownStationName-DowntownStationName" format, with uptown stations always first.
    
    :param station1: The first station name.
    :param station2: The second station name.
    :return: A string in the format "UptownStationName-DowntownStationName" or None if not adjacent.
    """
    
    # Check if the pair exists in the list
    if (station1, station2) in adjacent_stations:
        return f"{station1}-{station2}"
    elif (station2, station1) in adjacent_stations:
        return f"{station2}-{station1}"
    
    # Return None if not adjacent
    return None

# copied straight from chat
#! Known bug: Can't get all, fails to switch lines
def get_station_route(start_end_station_tuple):
    """
    Given two station names, returns a route that connects them using adjacent stations.
    The route is a list of station pairs in the format ["first station", "first station-second station", ..., "last station"].
    
    :param start_station: The starting station name.
    :param end_station: The destination station name.
    :return: A list of route segments, where each segment is formatted as "first station-second station".
    """
    # Create adjacency list
    (start_station, end_station) = start_end_station_tuple

    adjacency_list = {}
    for station1, station2 in adjacent_stations:
        if station1 not in adjacency_list:
            adjacency_list[station1] = []
        if station2 not in adjacency_list:
            adjacency_list[station2] = []
        adjacency_list[station1].append(station2)
        adjacency_list[station2].append(station1)
    
    # BFS setup
    queue = deque([(start_station, [])])  # Queue holds (current_station, path_taken_so_far)
    visited = set()  # To track visited stations

    # BFS to find the shortest path
    while queue:
        current_station, path = queue.popleft()
        
        # If we reached the destination
        if current_station == end_station:
            # Append the final station
            route = path + [current_station]
            # Format the path in the required "station1-station2" format
            route_segments = []
            for i in range(len(route) - 1):
                segment = get_adjacent_station_pair(route[i], route[i+1])
                route_segments.append(segment)
            return [route[0]] + route_segments + [route[-1]]
    
        # Mark the station as visited
        if current_station not in visited:
            visited.add(current_station)
            
            # Enqueue all adjacent stations that haven't been visited
            for neighbor in adjacency_list.get(current_station, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [current_station]))
    
    return ["No route found"]

# pass a pandas df, prints the best fit distribution
def determine_best_fit(data_points, plot = False):
    f = Fitter(data_points,
           distributions=['gamma',
                          'lognorm',
                          "beta",
                          "burr",
                          "norm"])
    f.fit()
    f.summary()
    if plot:
        plt.figure(figsize=(10, 6))
        plt.show()

    return f.get_best(method = 'sumsquare_error')

# given a dictionary with lists as values
# returns new dictionary with (mean, std dev) as values
def dict_mean_sd(dictionary):
    result = {key: (np.mean(value), np.std(value)) for key, value in dictionary.items()}
    return result

# takes a commuter (list of start station, segments, end station), and mean and std deviations for all stations PM, segments PM, and segments Time, num to simulate
# generates a monte carlo of the commuter's concentration * time
# returns commuter's concentration * time dist, time dist
# assumes 5 minute station wait time, plus or minus 2 mins
def generate_commuter_exp_dist(commuter = None, all_stations_PM_mean_sd = None, all_segments_PM_mean_sd = None , all_segments_Time_mean_sd = None, num_to_sim = 1000):
    # check for bad data

    commuter_exp_dist = []
    commuter_time_dist = []
    start_station = commuter[0]
    end_station = commuter[-1]
    (start_station_PM_mean, start_station_PM_sd) = all_stations_PM_mean_sd[start_station]
    (end_station_PM_mean, end_station_PM_sd) = all_stations_PM_mean_sd[end_station]
    commuter_segments = commuter[1:-1]
    station_Time_mean = 5
    station_Time_sd = 2

    current_exposure = 0
    current_time = 0
    # run num_to_sim samples
    for i in range(num_to_sim):
        # sample from a normal distribution of the start and end station
        time_sample1 = np.random.normal(station_Time_mean, station_Time_sd)
        time_sample2 = np.random.normal(station_Time_mean, station_Time_sd)

        # add start and end PM*time sample to current_exposure
        current_exposure += np.random.normal(start_station_PM_mean, start_station_PM_sd) * time_sample1
        current_exposure += np.random.normal(end_station_PM_mean, end_station_PM_sd) * time_sample2
        # add start and end time to current_time
        current_time += time_sample1 + time_sample2

        for num, segment  in enumerate(commuter_segments):
            # get PM and time data from this segment
            (segment_PM_mean, segment_PM_sd) = all_segments_PM_mean_sd[segment]
            (segment_Time_mean, segment_Time_sd) = all_segments_Time_mean_sd[segment]

            # sample time, multiply by PM sample and add to exposure
            segment_time_sample = np.random.normal(segment_Time_mean, segment_Time_sd)
            segment_exposure = np.random.normal(segment_PM_mean, segment_PM_sd) * segment_time_sample
            current_exposure += segment_exposure
            current_time += segment_time_sample
        
        commuter_time_dist.append(current_time)
        commuter_exp_dist.append(current_exposure)
        current_exposure = 0
        current_time = 0
    
    return (commuter_exp_dist, commuter_time_dist)

# little helper to make a pretty string for printing a commute
def commute_string_maker(commute_tuple, commute_time_dist):
    return commute_tuple[0] + ' to ' + commute_tuple[1] + ' (~' + str(round(np.mean(commute_time_dist), 1)) + ' mins)'

def main():
    # file_path = input("Feed me the csv file_path.")
    file_paths = ['./csvs/red1.csv', './csvs/red2.csv', './csvs/yellow1.csv', './csvs/yellow2.csv']
    data = load_csv(file_paths)
    num_to_sim = 5000

    if data is not None:
        (red_df, yellow_df) = data
        (red_stations_PM, red_segments_PM, red_segments_Time) = get_pm_and_time(clean_data(red_df), "red", True)
        (yellow_stations_PM, yellow_segments_PM, yellow_segments_Time) = get_pm_and_time(clean_data(yellow_df), "yellow", True)

        # concat red and yellow dictionaries
        all_stations_PM = red_stations_PM | yellow_stations_PM
        all_segments_PM = red_segments_PM | yellow_segments_PM
        all_segments_Time = red_segments_Time | yellow_segments_Time

        # find mean and sd for all values in each dictionary
        all_stations_PM_mean_sd = dict_mean_sd(all_stations_PM)
        all_segments_PM_mean_sd = dict_mean_sd(all_segments_PM)
        all_segments_Time_mean_sd = dict_mean_sd(all_segments_Time)

        # # check best fit for each station
        # for station in list(all_stations_PM.keys()):
        #     determine_best_fit(all_stations_PM[station], True)
        #     keep_going = input("Continue? ")
        #     if keep_going != "y" and keep_going != "Y" and keep_going != "":
        #         break

        #! assume 'Rockridge-MacArthur' same as "Orinda-Rockridge"
        all_segments_PM_mean_sd['Rockridge-MacArthur'] = all_segments_PM_mean_sd['Orinda-Rockridge']
        all_segments_Time_mean_sd['Rockridge-MacArthur'] = all_segments_Time_mean_sd['Orinda-Rockridge']
        warnings.warn("ALERT: Remember, we assume Rockridge-MacArthur same as Orinda-Rockridge")

        # make some commuters, get their routes
        commuterA = ("24th St Mission", "West Oakland")
        commuterB = ("Downtown Berkeley", "24th St Mission")
        commuterC = ("Walnut Creek", "Powell St")
        commuterD = ("Walnut Creek", "Orinda")

        # get their commutes
        commuteA = get_station_route(commuterA)
        commuteB = get_station_route(commuterB)
        commuteC = get_station_route(commuterC)
        commuteD = get_station_route(commuterD)

        # get distributions for each commuters exposure
        commuterA_exp_dist, commuterA_time_dist = generate_commuter_exp_dist(commuteA, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, num_to_sim)
        commuterB_exp_dist, commuterB_time_dist = generate_commuter_exp_dist(commuteB, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, num_to_sim)
        commuterC_exp_dist, commuterC_time_dist = generate_commuter_exp_dist(commuteC, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, num_to_sim)
        commuterD_exp_dist, commuterD_time_dist = generate_commuter_exp_dist(commuteD, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, num_to_sim)
        commuters_exp_dist = [commuterA_exp_dist, commuterB_exp_dist, commuterC_exp_dist, commuterD_exp_dist]

        # plot those distributions
        commute_strings = [commute_string_maker(commuterA, commuterA_time_dist), commute_string_maker(commuterB, commuterB_time_dist), commute_string_maker(commuterC, commuterC_time_dist), commute_string_maker(commuterD, commuterD_time_dist)]
        plot_list_of_distributions(commuters_exp_dist, commute_strings, ("Commuters PM exposure compared", "(ug * min)/m^3", "Density"))


if __name__ == "__main__":
    main()
