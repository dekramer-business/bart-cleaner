from fitter import Fitter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression


# pass a pandas df, prints the best fit distribution
def determine_best_fit(data_points, plot = False):
    f = Fitter(data_points,
           distributions=['gamma',
                          'lognorm',
                          "beta",
                        #   "burr",
                          "norm"])
    f.fit()
    f.summary()
    if plot:
        plt.figure(figsize=(10, 6))
        plt.show()

    return f.get_best(method = 'sumsquare_error')

def plot_list_of_tuples(list_of_tuples=None, name_x_y=("Scatter Plot of Tuples", 'X-axis', 'Y-axis')):
    """
    Plots a list of tuples (x, y) as a scatter plot with a single regression line.
    
    :param list_of_tuples: A list of (x, y) tuples to plot.
    :param name_x_y: A tuple containing the plot title, x-axis label, and y-axis label.
    """
    if list_of_tuples is None or not list_of_tuples:
        return None

    # Set Seaborn style for a clean, minimalistic plot
    sns.set(style="whitegrid")

    plt.figure(figsize=(10, 6))

    # Extract x and y values
    x_values = np.array([t[0] for t in list_of_tuples]).reshape(-1, 1)
    y_values = np.array([t[1] for t in list_of_tuples])

    # Create scatter plot for the data points (smaller points)
    plt.scatter(x_values, y_values, color="blue", s=30, edgecolors="black", alpha=0.7)

    # Fit a linear regression model
    model = LinearRegression()
    model.fit(x_values, y_values)
    y_pred = model.predict(x_values)

    # Plot the regression line
    plt.plot(x_values, y_pred, color="red", linewidth=2, label="Regression Line")

    # Title and axis labels with styling
    plt.title(name_x_y[0], fontsize=16, fontweight='bold', color='#2C3E50')
    plt.xlabel(name_x_y[1], fontsize=14, fontweight='bold', color='#34495E')
    plt.ylabel(name_x_y[2], fontsize=14, fontweight='bold', color='#34495E')

    # Customizing the grid and tick marks
    plt.grid(True, which='both', linestyle='--', color='gray', alpha=0.3)
    plt.xticks(fontsize=12, fontweight='light')
    plt.yticks(fontsize=12, fontweight='light')

    # Show the plot with a legend
    plt.legend()
    plt.tight_layout()  # Ensure labels fit well
    plt.show()

# alternates between red and blue and solid and dashed lines for plotting distributions
def plot_list_of_distributions(list_of_distributions=None, list_of_distribution_names=None, name_x_y=("Multiple Normal Distributions", 'Value', 'Density')):
    if list_of_distributions is None:
        return None

    plt.figure(figsize=(10, 6))

    # Define line styles and fixed colors
    line_styles = ['-', '--']  # Solid and dashed lines
    colors = ['red', 'blue']  # Red for first pair, blue for second, and so on

    for i, distribution in enumerate(list_of_distributions):
        color_index = i // 2  # Pair distributions with the same color
        line_style = line_styles[i % 2]  # Alternate between solid and dashed
        
        sns.kdeplot(
            distribution, 
            label=list_of_distribution_names[i] if list_of_distribution_names else f"Distribution {i + 1}", 
            color=colors[color_index % len(colors)],  # Alternate between red and blue
            linestyle=line_style,
            linewidth=3
        )

    plt.xlabel(name_x_y[1])
    plt.ylabel(name_x_y[2])
    plt.legend()
    plt.title(name_x_y[0])
    plt.show()

