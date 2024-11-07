from numpy.random import default_rng
import numpy as np
import plotly.express as px
import pandas as pd

def load_csv():
    # Prompt user to enter the CSV file path
    # file_path = input("Enter the path to the CSV file: ")
    file_path = './csvs/red1.csv'
    
    try:
        # Read the CSV file
        data = pd.read_csv(file_path)
        print("File loaded successfully!")
        return data
    except FileNotFoundError:
        print("File not found. Please check the path and try again.")
    except pd.errors.EmptyDataError:
        print("The file is empty.")
    except pd.errors.ParserError:
        print("Error parsing the file. Please check the file format.")
    return None

def clean_data(data):
    # Placeholder function where you can add data cleaning steps
    print("Cleaning data...")
    # Add your cleaning code here
    return data

def save_data(data):
    # Prompt user to enter the output file path
    output_path = input("Enter the path to save the cleaned CSV file (e.g., output.csv): ")
    try:
        # Save the DataFrame to the specified path
        data.to_csv(output_path, index=False)
        print(f"Data saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving the file: {e}")

def main():
    # Load the data
    data = load_csv()
    if data is not None:
        print("Initial data preview:")
        print(data.head())  # Display the first few rows
        # Clean the data if needed
        data = clean_data(data)
        print("Data cleaned (if any cleaning steps were added).")
        # Save the cleaned data
        save_data(data)

if __name__ == "__main__":
    main()
