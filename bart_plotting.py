from fitter import Fitter
import matplotlib.pyplot as plt
import seaborn as sns


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


import matplotlib.pyplot as plt
import seaborn as sns

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

