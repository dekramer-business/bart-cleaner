import numpy as np
import pandas as pd
from raw_csv_handling import *
from station_handling import *
from bart_plotting import *

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

# save data to a csv
def save_data_csv(data):
    # Prompt user to enter the output file path
    output_path = input("Enter the path to save the cleaned CSV file (e.g., output.csv): ")
    try:
        data.to_csv(output_path, index=False)
        print(f"Data saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving the file: {e}")

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
def commuter_string_helper(commute_tuple, commute_time_dist):
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
        custom_warn("ALERT: Remember, we assume Rockridge-MacArthur same as Orinda-Rockridge")

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
        commute_strings = [commuter_string_helper(commuterA, commuterA_time_dist), commuter_string_helper(commuterB, commuterB_time_dist), commuter_string_helper(commuterC, commuterC_time_dist), commuter_string_helper(commuterD, commuterD_time_dist)]
        plot_list_of_distributions(commuters_exp_dist, commute_strings, ("Commuters PM exposure compared", "(ug * min)/m^3", "Density"))


if __name__ == "__main__":
    main()
