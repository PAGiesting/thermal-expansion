# thermal-expansion
Calculates linear and volume alphas from dilatometer data (Netzsch DIL-402c) by curve fitting.

Initial plan is to use scipy.optimize to fit the raw expansion data and calculate a derivative from this fitted curve.
The linear alpha (thermal expansion coefficient) is the derivative of the quantity delta-length / length.
This data is continuous and once-differentiable, but alphas calculated by direct differentiation are noisy.
Smoothing these noisy alphas via curve fitting or moving averages is an alternative option, but the results via spreadsheet
did not look promising.
