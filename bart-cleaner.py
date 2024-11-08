from numpy.random import default_rng
import numpy as np
import plotly.express as px
import pandas as pd

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

    print(red_combined_df)
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

def main():
    # file_path = input("Feed me the csv file_path.")
    file_paths = ['./csvs/red1.csv', './csvs/red2.csv', './csvs/yellow1.csv', './csvs/yellow2.csv']
    data = load_csv(file_paths)
    if data is not None:
        (red_df, yellow_df) = data
        red_df = clean_data(red_df)
        yellow_df = clean_data(yellow_df)
        print(red_df.head())
        print(red_df.shape[0])  # num rows

if __name__ == "__main__":
    main()
