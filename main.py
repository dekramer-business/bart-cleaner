import numpy as np
import pandas as pd
from scipy.stats import pearsonr
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

import os

# Save data to a CSV
def save_data_csv(data, output_path=None):
    # Define the default folder
    default_folder = "saved_data"
    # Ensure the folder exists
    os.makedirs(default_folder, exist_ok=True)
    
    if output_path is None:
        # Prompt user for a file name and save it in the default folder
        file_name = input("Enter the file name to save the cleaned CSV (e.g., output.csv): ")
        output_path = os.path.join(default_folder, file_name)
    else:
        # Ensure the output path is within the default folder
        output_path = os.path.join(default_folder, output_path)
    
    try:
        # Save the data to the specified path
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

# given a station, returns (average time, sd) of that station
def generate_station_time(station):
    color = station_colors[station]

    if color == "yellow":
        if station == "Pittsburg Center" or station == "Antioch":
            return (5, 2)
        else:
            return (5, 2)
    return (5, 2)

# calc dose based on epa
# units are ug / (BW * day)
def calculate_dose(C, IR, CF, ED, EF, AT, BW):
    # print(f"C: {C}, IR: {IR}, CF: {CF}, ED: {ED}, EF: {EF}, AT: {AT}, BW: {BW}")

    # Minutes per day
    mins_per_day = 1440

    # make ED in days
    ED = ED/mins_per_day

    top = C * IR * CF * ED * EF
    bottom = AT * BW

    return top/bottom

# takes a commuter (start station, end station), and mean and std deviations for all stations PM, segments PM, and segments Time, num to simulate
# generates a monte carlo of the commuter's dose
# returns commuter's dose dist, time dist
# assumes 5 minute station wait time, plus or minus 2 mins
def generate_commute_dose_distribution(commuter = None, all_stations_PM_mean_sd = None, all_segments_PM_mean_sd = None , all_segments_Time_mean_sd = None, using_male_data = True, num_to_sim = 1000, times_per_day = 2):
    #! check for bad data
    if commuter is None:
        return float('inf')

    commute = get_station_route(commuter)

    # get station data
    commuter_dose_dist = []
    commuter_time_dist = []
    start_station = commute[0]
    end_station = commute[-1]
    (start_station_PM_mean, start_station_PM_sd) = all_stations_PM_mean_sd[start_station]
    (end_station_PM_mean, end_station_PM_sd) = all_stations_PM_mean_sd[end_station]

    # parse commute
    commuter_segments = commute[1:-1]

    # get time mean, sd for both stations
    start_station_Time_mean, start_station_Time_sd = generate_station_time(start_station)
    # end_station_Time_mean, end_station_Time_sd = generate_station_time(end_station)
    end_station_Time_mean, end_station_Time_sd = (2,1)

    # set average body weight
    if using_male_data:
        BW = 90.7185
    else:
        BW = 77.1107
    
    # average IR in m^3/day
    IR = 16

    current_dose = 0
    current_time = 0
    # run num_to_sim samples
    for i in range(num_to_sim):
        # sample from a normal distribution of the start and end station
        start_station_ED = np.random.normal(start_station_Time_mean, start_station_Time_sd)
        end_station_ED = np.random.normal(end_station_Time_mean, end_station_Time_sd)

        # add start and end time to current_time
        current_time += start_station_ED + end_station_ED

        # add start and end dose sample to current_dose
        start_station_PM_sample = np.random.normal(start_station_PM_mean, start_station_PM_sd)
        end_station_PM_sample = np.random.normal(end_station_PM_mean, end_station_PM_sd)
        # print("start_station name: ", start_station)
        start_dose = calculate_dose(start_station_PM_sample, IR, 1, start_station_ED, times_per_day, 1, BW)
        end_dose = calculate_dose(end_station_PM_sample, IR, 1, end_station_ED, times_per_day, 1, BW)
        current_dose += start_dose + end_dose

        for num, segment  in enumerate(commuter_segments):
            # get PM and time data from this segment
            (segment_PM_mean, segment_PM_sd) = all_segments_PM_mean_sd[segment]
            (segment_Time_mean, segment_Time_sd) = all_segments_Time_mean_sd[segment]

            # sample time, multiply by PM sample and add to exposure
            segment_time_sample = np.random.normal(segment_Time_mean, segment_Time_sd)
            segment_PM_sample = np.random.normal(segment_PM_mean, segment_PM_sd)
            current_dose += calculate_dose(segment_PM_sample, IR, 1, segment_time_sample, times_per_day, 1, BW)

            # Sum time on segment
            current_time += segment_time_sample
        
        commuter_time_dist.append(current_time)
        commuter_dose_dist.append(current_dose)
        current_dose = 0
        current_time = 0
    
    return (commuter_dose_dist, commuter_time_dist)

# little helper to make a pretty string for printing a commute
def commuter_string_helper(commute_tuple, commute_time_dist = None):
    if commute_time_dist is not None:
        return commute_tuple[0] + ' to ' + commute_tuple[1] + ' (~' + str(round(np.mean(commute_time_dist), 1)) + ' mins)'
    else:
        return commute_tuple[0] + ' to ' + commute_tuple[1]
    
# generate, plot, analyze all commutes of n length
def analyze_all_possible_commutes(all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, stations_n_distance):
    if None in [all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, stations_n_distance]: 
        return None

    # Generate all start and stop combinations with n total stations in the commute
    stations_n_apart = get_station_pairs_with_min_distance(stations_n_distance)

    # For each commute generate a distribution, then find mean of pm and time (is that redundant?)
    all_doses_and_ground_percents = []
    all_percent_below_ground = []  # for pearson test
    all_dose_per_time = []  # for pearson test
    for commute in stations_n_apart:
        times_per_day = 1 # say per day
        commute_dose_dist, commute_time_dist = generate_commute_dose_distribution(commute, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, times_per_day)
        commute_dose_mean = sum(commute_dose_dist) / len(commute_dose_dist)
        commute_time_mean = sum(commute_time_dist) / len(commute_time_dist)
        commute_dose_per_time = commute_dose_mean/(commute_time_mean * times_per_day)

        commute_below_percent = get_below_station_percent(commute)
        all_doses_and_ground_percents.append((commute_below_percent, commute_dose_per_time))
        all_percent_below_ground.append(commute_below_percent)
        all_dose_per_time.append(commute_dose_per_time)

    if using_male_data:
        dose_name = "Dose / Commute Time  [ug/(kg * min)]"
        plot_name = "Male Dose/Time vs Percent Below Ground"
    else:
        dose_name = "Dose / Commute Time  [ug/(kg * min)]"
        plot_name = "Female Dose/Time vs Percent Below Ground"

    plot_list_of_tuples(all_doses_and_ground_percents, (plot_name, "Percent of Commute Below Ground", dose_name))

    # Pearson's correlation on all_percent_below_ground vs all_dose_per_time
    pearson_r, p_value = pearsonr(all_percent_below_ground, all_dose_per_time)
    print(f"Pearson's r: {round(pearson_r, 3)}, p-value: {p_value:.3e}")

# analyze 4 commuters more in depth
def analyze_compare_some_commutes(all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, save_to_csv = False):
    if None in [all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim]: 
        return None

    # make some commuters, get their routes
    commuterA = ("24th St Mission", "Embarcadero")
    commuterB = ("Downtown Berkeley", "24th St Mission")
    commuterC = ("Walnut Creek", "Embarcadero")
    commuterD = ("Pittsburg/Bay Point", "Rockridge")

    # get distributions for each commuters exposure, save to dictionary   
    times_per_day = 1 # say per day
    commuterB_exp_dist, commuterB_time_dist = generate_commute_dose_distribution(commuterB, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, times_per_day)
    commuterC_exp_dist, commuterC_time_dist = generate_commute_dose_distribution(commuterC, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, times_per_day)
    commuterD_exp_dist, commuterD_time_dist = generate_commute_dose_distribution(commuterD, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, times_per_day)
    commuterA_exp_dist, commuterA_time_dist = generate_commute_dose_distribution(commuterA, all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, times_per_day)
    
    # Create a list of commuter names and their exposure/time distributions
    commuters = [
        (commuter_string_helper(commuterA), commuterA_exp_dist, commuterA_time_dist),
        (commuter_string_helper(commuterB), commuterB_exp_dist, commuterB_time_dist),
        (commuter_string_helper(commuterC), commuterC_exp_dist, commuterC_time_dist),
        (commuter_string_helper(commuterD), commuterD_exp_dist, commuterD_time_dist)
    ]

    # Plot distributions (optional)
    commute_strings = [commuter[0] for commuter in commuters]
    if using_male_data:
        plot_name = "Male Commuters Dose Compared"
        file_name = "male_commuters_dose_time.csv"
    else:
        plot_name = "Female Commuters Dose Compared"
        file_name = "female_commuters_dose_time.csv"
    plot_list_of_distributions([commuter[1] for commuter in commuters], commute_strings, (plot_name, "ug/kg", "Density"))

    # Save data to CSV if needed
    if save_to_csv:
        print("Saving commuter dose data to CSV")
        
        # Prepare the data for CSV
        data_to_save = []
        for commuter_name, exp_dist, time_dist in commuters:
            avg_dose = sum(exp_dist) / len(exp_dist)
            dose_std = np.std(exp_dist)  # Standard deviation of the exposure
            avg_time = sum(time_dist) / len(time_dist)
            time_std = np.std(time_dist)  # Standard deviation of the time

            data_to_save.append([commuter_name, avg_dose, dose_std, avg_time, time_std])
        
        # Create DataFrame
        df = pd.DataFrame(data_to_save, columns=["Commute Name", "Average Dose", "Dose Standard Deviation", "Average Time", "Time Standard Deviation"])
        save_data_csv(df, file_name)


def main():
    # file_path = input("Feed me the csv file_path.")
    file_paths = ['./csvs/red1.csv', './csvs/red2.csv', './csvs/yellow1.csv', './csvs/yellow2.csv']
    data = load_csv(file_paths)

    # params
    num_to_sim = 500000
    using_male_data = True
    save_to_csv = True

    # alert on what data
    if using_male_data:
        custom_warn("ALERT: Using MALE weight data")
    else:
        custom_warn("ALERT: Using FEMALE weight data")

    if data is not None:
        # Get data
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

        #! assume 'Rockridge-MacArthur' same as "Orinda-Rockridge"
        all_segments_PM_mean_sd['Rockridge-MacArthur'] = all_segments_PM_mean_sd['Orinda-Rockridge']
        all_segments_Time_mean_sd['Rockridge-MacArthur'] = all_segments_Time_mean_sd['Orinda-Rockridge']
        custom_warn("ALERT: Assuming Rockridge-MacArthur same as Orinda-Rockridge")

        # analyze_all_possible_commutes(all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, 5)

        analyze_compare_some_commutes(all_stations_PM_mean_sd, all_segments_PM_mean_sd, all_segments_Time_mean_sd, using_male_data, num_to_sim, save_to_csv)
        

if __name__ == "__main__":
    main()
