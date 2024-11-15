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
