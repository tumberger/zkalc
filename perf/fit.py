import sys
import math
import json
from collections import defaultdict

import numpy as np
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt

class NoNeedForFitting(Exception): pass

RESULTS_FNAME = "coefficients.json"

def parse_benchmark_description(description):
    description = description.split("/")

    match description[0]:
        case "msm":
            desc = "MSM_" + description[1]
            return desc, description[2]
        case _:
            raise NoNeedForFitting

def to_nanoseconds(num, unit_str):
    """Convert `num` in `unit_str` to nanoseconds"""
    match unit_str:
        case "ns":
            return num
        case "ms":
            return num * 1e6
        case "s":
            return num * 1e9
        case _:
            raise

def plot_func(data, func):
    # Get the sizes and times from the data
    sizes, times = zip(*data.items())
    # Convert the times from nanoseconds to seconds
    times = [time / 1e9 for time in times]

    # Generate a range of sizes to use for the plot
    size_range = np.linspace(min(sizes), max(sizes), 100)
    # Compute the predicted times for the size range
    predicted_times = func(size_range)
    # Convert the predicted times from nanoseconds to seconds
    predicted_times = [time / 1e9 for time in predicted_times]

    # Create a new figure and plot the actual data
    plt.figure()
    plt.scatter(sizes, times, label='Actual data')
    # Plot the fitted linear function
    plt.plot(size_range, predicted_times, label='Linear fit')
    plt.xlabel('Size')
    plt.ylabel('Time (in seconds)')
    plt.legend()
    plt.show()

def plot_error(data, func):
    # Get the sizes and times from the data
    sizes, times = zip(*data.items())

    # Calculate the error between the actual and predicted values
    errors = []
    for i, size in enumerate(sizes):
        error = times[i] - func(sizes[i])
        print("Error: %s for time %s vs predicted time %s" % (error / 1e9, times[i] / 1e9 , func(sizes[i]) / 1e9))
        errors.append(abs(error))

    plt.semilogx(sizes, errors, 'bo', label='Errors', base=2)
    plt.xlabel('Sizes')
    plt.ylabel('Errors')
    plt.title('Errors at different sizes')
    plt.legend()
    plt.show()

def fit_poly_to_data(data):
    """Basic linear regression: Extract a linear polynomial from the data"""

    # Get the sizes and times from the data
    sizes, times = zip(*data.items())
    # Use NumPy's polyfit function to fit a linear curve
    polynomial = poly.Polynomial.fit(sizes, times, deg=1)

#    plot_func(data, polynomial)
#    plot_error(data, polynomial)

    # Return the fitted func
    return polynomial

def extract_measurements(bench_output):
    # Nested dictionary with benchmark results in the following format: { operation : {msm_size : time_in_microseconds }}
    measurements = defaultdict(dict)
    # Dictionary of results in format: { operation : fitted_coefficients }
    results = {}

    # Parse benchmarks and make them ready for fitting
    for measurement in bench_output:
        # Skip useless non-benchmark lines
        if "id" not in measurement:
            continue

        # Extra data from json
        try:
            operation, size = parse_benchmark_description(measurement["id"])
        except NoNeedForFitting:
            continue

        measurement_in_ns = to_nanoseconds(measurement["mean"]["estimate"], measurement["mean"]["unit"])
        measurements[operation][int(size)] = measurement_in_ns

    # Fit benchmark data to polynomial
    for operation in measurements.keys():
        poly = fit_poly_to_data(measurements[operation])
        coeffs = ["%d" % (coeff) for coeff in poly]
        results[operation] = coeffs
        print("%s [%s samples] [2^28 example: %0.2f s]:\n\t%s\n" % (operation, len(measurements[operation]), poly(2**28)/1e9, coeffs))

    # Write results to json file
    with open(RESULTS_FNAME, "w") as f:
        # Encode the coefficients as a JSON object
        json_data = json.dumps(results)
        # Write the JSON object to the file
        f.write(json_data)

    print("[!] Wrote results to '%s'! Bye!" % (RESULTS_FNAME))

def main():
    if len(sys.argv) < 1:
        print("fit.py estimates.json")
        sys.exit(1)

    bench_output = []
    with open(sys.argv[1]) as f:
        for line in f:
            bench_output.append(json.loads(line))

    extract_measurements(bench_output)

if __name__ == '__main__':
    main()
