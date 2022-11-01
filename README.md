# Split Conformal Prediction for Non-Exchangeable Data

This repository contains the code for the paper "Split Conformal Prediction for Non-Exchangeable Data" (Roberto I. Oliveira, Paulo Orenstein, Thiago Ramos, João Vitor Romano).

## Setup

- All scripts should be run from the git repository root directory (`split-conformal-nonexchangeable/`).
- Packages listed in `requirements.txt` should be installed via your python package manager of choice.
- Python 3.10+ is required.

## Structure

- **src**: project source code (pushed to the repository).
- **data**: raw and processed datasets.
- **eval**: plots, tables and other output used to evaluate coverage.

## Usage example

We give below a simple example of how the code in this repository can be used for data generation, conformal prediction and coverage evaluation.

```
from src.models import ConformalizedQR, RandomForestQR
from src.utils.data import get_synthetic
from src.utils.eval import empirical_coverage

# Generate data from a nonexchangeable autoregressive process
data = get_synthetic("ar1", N=1500, lags=10, seed=0, phi=0.8)

# Split the data into features and target
X, y = data.drop("target", axis=1), data["target"]

# Partition into training, calibration and test sets
X_train, y_train = X[:500], y[:500]
X_cal, y_cal = X[500:1000], y[500:1000]
X_test, y_test = X[1000:], y[1000:]

# Fit, calibrate and generate prediction intervals for a prescribed coverage level of 90%
cqr = ConformalizedQR(Model=RandomForestQR, alpha=0.1, seed=0)
cqr.fit(X_train, y_train)
cqr.calibrate(X_cal, y_cal)
y_pred_lower, y_pred_upper = cqr.predict(X_test)

# Evaluate coverage
empirical_coverage(y_test, y_pred_lower, y_pred_upper)
```

## Generate figures and table

### Figures 1 and 2

- Run `sh src/paper/synthetic-marginal_coverage.sh` to generate the results.
- Run `python src/eval/synthetic/plot-marginal_coverage.py --stochastic_process ar1` to plot.
- Run `python src/eval/synthetic/plot-marginal_coverage.py --stochastic_process two_state_markov_chain` to plot.

### Figure 3a

- Run `sh src/paper/theoretical_guarantee.sh` to generate the results.
- Run `python src/eval/synthetic/plot-theoretical_guarantee.py` to plot.

### Figure 3b

- Run `sh src/paper/synthetic-empirical_coverage.sh` to generate the results.
- Run `python src/eval/synthetic/plot-empirical_coverage.py` to plot.

### Download and process financial data

- Run `python src/data/download.py` to download the data.
- Run `sh src/paper/real_datasets-process.sh` to generate the datasets.

### Figure 4

- Run `python src/eval/real/marginal_coverage.py --dataset eurusd` to generate the results.
- Run `python src/eval/real/marginal_coverage.py --dataset bcousd` to generate the results.
- Run `python src/eval/real/marginal_coverage.py --dataset spxusd` to generate the results.
- Run `python src/eval/real/plot-marginal_coverage.py` to plot.

### Table 1

- Run `sh src/paper/real-conditional_coverage.sh` to generate the results.
- Run `python src/eval/real/table-conditional_coverage.py` to create the table.
