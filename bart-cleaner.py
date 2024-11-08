from numpy.random import default_rng
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
    cols_to_keep = ["Color", "PM2.5 (ug/m3)", "PM2.5 (ug/m3).1", "Station", "N/S", "Station"]
    data = data.drop(columns=list(filter(lambda col: col not in cols_to_keep, data.columns)))
    # Add your cleaning code here
    return data

def save_data(data):
    # Prompt user to enter the output file path
    output_path = input("Enter the path to save the cleaned CSV file (e.g., output.csv): ")
    try:
        data.to_csv(output_path, index=False)
        print(f"Data saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving the file: {e}")

# give data_points, number of points, whether to plot the distr.
# returns normal distribution
def norm_generator(data_points, num_points, plot_it = False):
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
        print(yellow_df.head())
        # print(yellow_df.shape[0])  # num rows

        data_points = [2, 5, 16, 15.5, 17, 14.8, 16.2, 15.6, 16.5]

if __name__ == "__main__":
    main()
