from numpy.random import default_rng
import math
import numpy as np
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

# given some data_points, number of points to simulate, whether to plot the distr.
# returns a list of points using normal distribution
def norm_generator(data_points = None, num_points = 1000, plot_it = False):
    if data_points == None: return None
    mean = np.mean(data_points)
    std_dev = np.std(data_points)

    # generate normal distribution
    normal_dist = np.random.normal(mean, std_dev, num_points)

    if plot_it:
        sns.kdeplot(normal_dist, label="Generated Normal Distribution", color="blue")

        # Label x and y axis, 
        plt.xlabel("Value")
        plt.ylabel("Density")
        plt.legend()
        plt.title("Normal Distribution")
        plt.show()
    
    return normal_dist

# given a cleaned df containing minute-by-minute measurements
# return three dictionarys (stations_PM, segments_PM, segment_Time)
# stations_PM will have stations as keys, a list of all PM measurements as the value
# segments_PM will have segments as keys, a list of all PM measurements as the value
# segments_Time will have segments as keys, a list of all the number of minutes on that segment for each trip (should be length 8)
def get_pm_and_time(cleaned_df, line_color):
    stations_PM = {}
    segments_PM = {}
    segments_Time = {}
    
    if line_color == "red":
        last_station = None
        between_station_buffer = []
        for row in cleaned_df.itertuples():
            station_name = row.Station
            if row.Direction == 'Southbound':  # keeping stations and segments

                # if were on the train
                if station_name == 'Between Stations':
                    # get PM measurements
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20
                    # only append if measurement is a number
                    if not math.isnan(PM2_5_19):
                        between_station_buffer.append(PM2_5_19)
                    if not math.isnan(PM2_5_20):
                        between_station_buffer.append(PM2_5_20)
                else:
                    # we hit a new station, add the buffer to segments_PM and segments_PM time
                    if (last_station is not None) and (last_station is not station_name):
                        segment_name = last_station + '-' + station_name

                        # catch dictionary doesnt have key case
                        if segment_name not in segments_PM:
                            segments_PM[segment_name] = []
                            segments_Time[segment_name] = []

                        # add the between station PM and Time data
                        segments_PM[last_station + '-' + station_name].extend(between_station_buffer)
                        segments_Time[last_station + '-' + station_name].append(len(between_station_buffer)/2)

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
                    # get PM measurements
                    PM2_5_19 = row.PM2_5_19
                    PM2_5_20 = row.PM2_5_20
                    # only append if measurement is a number
                    if not math.isnan(PM2_5_19):
                        between_station_buffer.append(PM2_5_19)
                    if not math.isnan(PM2_5_20):
                        between_station_buffer.append(PM2_5_20)
                else:
                    # we hit a new station, add the buffer to segments_PM and segments_PM time
                    if (last_station is not None) and (last_station is not station_name):
                        segment_name = station_name + '-' + last_station

                        # catch dictionary doesnt have key case
                        if segment_name not in segments_PM:
                            segments_PM[segment_name] = []
                            segments_Time[segment_name] = []

                        # add the between station PM and Time data
                        segments_PM[station_name + '-' + last_station].extend(between_station_buffer)
                        segments_Time[station_name + '-' + last_station].append(len(between_station_buffer)/2)

                    # set this station as the last station
                    last_station = station_name
                    between_station_buffer = []
                    

    return (stations_PM, segments_PM, segments_Time)


def main():
    # file_path = input("Feed me the csv file_path.")
    file_paths = ['./csvs/red1.csv', './csvs/red2.csv', './csvs/yellow1.csv', './csvs/yellow2.csv']
    data = load_csv(file_paths)
    if data is not None:
        (red_df, yellow_df) = data
        red_df = clean_data(red_df)
        yellow_df = clean_data(yellow_df)
        print(red_df.head())
        # print(red_df.shape[0])  # num rows
        # print(yellow_df.head())
        # print(yellow_df.shape[0])  # num rows

        # data_points = [2, 5, 16, 15.5, 17, 14.8, 16.2, 15.6, 16.5]
        # norm_generator(data_points, 500)

        print(get_pm_and_time(red_df, "red")[1])
        # print("((((((((((((((((((((((()))))))))))))))))))))))")
        # print(get_pm_and_time(red_df, "red")[2])

if __name__ == "__main__":
    main()
