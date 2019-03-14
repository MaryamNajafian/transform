# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for information-theoretic preprocessing algorithms."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math

import numpy as np


def calculate_partial_expected_mutual_information(n, x_i, y_j):
  """Calculates the partial expected mutual information (EMI) of two variables.

    EMI reflects the MI expected by chance, and is used to compute adjusted
    mutual information. See www.wikipedia.org/wiki/Adjusted_mutual_information.

    The EMI for two variables x and y, is the sum of the expected mutual info
    for each value of x with each value of y. This function computes the EMI
    for a single value of each variable (x_i, y_j) and is thus considered a
    partial EMI calculation.

    Specifically:
    EMI(x, y) = sum_{n_ij = max(0, x_i + y_j - n) to min(x_i, y_j)} (
      n_ij / n * log2((n * n_ij / (x_i * y_j))
      * ((x_i! * y_j! * (n - x_i)! * (n - y_j)!) /
      (n! * n_ij! * (x_i - n_ij)! * (y_j - n_ij)! * (n - x_i - y_j + n_ij)!)))
    where n_ij is the joint count of x taking on value i and y taking on
    value j, x_i is the count for x taking on value i, y_j is the count for y
    taking on value j, and n represents total count.

  Args:
    n: The sum of weights for all values.
    x_i: The sum of weights for the first variable taking on value i
    y_j: The sum of weights for the second variable taking on value j

  Returns:
    Calculated expected mutual information for x_i, y_j.
  """
  coefficient = (-np.log2(x_i) - np.log2(y_j) + np.log2(n))
  sum_probability = 0.0
  partial_result = 0.0
  for n_j, p_j in _hypergeometric_pmf(n, x_i, y_j):
    if n_j != 0:
      partial_result += n_j * (coefficient + np.log2(n_j)) * p_j
    sum_probability += p_j
  # With approximate calculations for log2(x) and exp2(x) with large x, we need
  # a correction to the probablity approximation, so we divide by the sum of the
  # probabilities.
  return partial_result / sum_probability


def calculate_partial_mutual_information(n_ij, x_i, y_j, n):
  """Calculates Mutual Information from sample counts.

  Given the formula for mutual information,
  MI(X,Y) = log2(N) + 1/N Sum_i,j {n_ij * (log2(n_ij / (x_ * y_j)))}
  this function returns the argument to the summation, the mutual information
  for a particular pair of values x_i, y_j.

  Args:
    n_ij: The co-occurrence of x=i and y=j
    x_i: The frequency of x=i.
    y_j: The frequency of y=j.
    n: The total # observations

  Returns:
    Mutual information for the cell x=i, y=j.
  """
  if n_ij == 0:
    return 0
  return n_ij * ((np.log2(n_ij) + np.log2(n)) - (np.log2(x_i) + np.log2(y_j)))


def _hypergeometric_pmf(n, x_i, y_j):
  """Probablity for expectation computation under hypergeometric distribution.

  Args:
    n: The sum of weights for all values.
    x_i: The sum of weights for the first variable taking on value i
    y_j: The sum of weights for the second variable taking on value j

  Yields:
    Calculated coefficient, numerator and denominator for hypergeometric
    distribution.
  """
  start = int(max(0, n - (n - x_i) - (n - y_j)))
  end = int(min(x_i, y_j))
  # Use log factorial to preserve calculation precision.
  # Note: because the factorials are expensive to compute, we compute the
  # denominator incrementally, at the cost of some readability.
  numerator = (
      _logfactorial(x_i) + _logfactorial(y_j) + _logfactorial(n - x_i) +
      _logfactorial(n - y_j))
  denominator = (
      _logfactorial(n) + _logfactorial(start) + _logfactorial(x_i - start) +
      _logfactorial(y_j - start) + _logfactorial(n - x_i - y_j + start))
  for n_j in range(start, end + 1):
    p_j = np.exp(numerator - denominator)
    denominator += (
        np.log(n_j + 1) - np.log(x_i - n_j) - np.log(y_j - n_j) +
        np.log(n - x_i - y_j + n_j + 1))
    yield n_j, p_j


def _logfactorial(n):
  """Calculate natural logarithm of n!."""
  return math.lgamma(n + 1)
