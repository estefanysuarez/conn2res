# -*- coding: utf-8 -*-
"""
Functions to train the readout module to perform
tasks

@author: Estefany Suarez
"""

import numpy as np
import pandas as pd
import scipy as sp
import mdp

from sklearn import metrics
from sklearn.model_selection import ParameterGrid
from sklearn.linear_model import Ridge, RidgeClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputRegressor, MultiOutputClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.ensemble import RandomForestRegressor

import matplotlib.pyplot as plt


def check_xy_dims(x,y):
    """
    Check that X,Y have the right dimensions
    #TODO
    """
    x_train, x_test = x
    y_train, y_test = y

    if ((x_train.ndim == 1) and (x_test.ndim == 1)):
        x_train = x_train[:, np.newaxis]
        x_test  = x_test[:, np.newaxis]
    elif ((x_train.ndim > 2) and (x_test.ndim > 2)):
        x_train = x_train.squeeze()
        x_test  = x_test.squeeze()

    y_train = y_train.squeeze()
    y_test  = y_test.squeeze()

    return x_train, x_test, y_train, y_test


def regression(x, y, **kwargs):
    """
    Regression tasks
    #TODO
    """

    x_train, x_test = x
    y_train, y_test = y

    model = Ridge(fit_intercept=False, alpha=0.5, **kwargs).fit(x_train, y_train)
    score = model.score(x_test, y_test)

    return score


def multiOutputRegression(x, y, **kwargs):
    """
    Multiple output regression tasks
    #TODO
    """

    x_train, x_test = x
    y_train, y_test = y

    model = MultiOutputRegressor(Ridge(fit_intercept=False, alpha=0.5, **kwargs)).fit(x_train, y_train)

    y_pred = model.predict(x_test)
    n_outputs = y_pred.shape[1]

    score = []
    for output in range(n_outputs):
        score.append(np.abs((np.corrcoef(y_test[:,output], y_pred[:,output])[0][1])))

    return np.sum(score)


def classification(x, y, **kwargs):
    """
    Binary classification tasks
    #TODO
    """

    x_train, x_test = x
    y_train, y_test = y

    model = RidgeClassifier(alpha=0.0, fit_intercept=True, **kwargs).fit(x_train, y_train)
    score  = model.score(x_test, y_test)

    # # confusion matrix
    # ConfusionMatrixDisplay.from_predictions(y_test, model.predict(x_test))
    # plt.show()
    # plt.close()

    return score


def multiClassClassification(x, y, **kwargs):
    """
    Multi-class Classification tasks
    #TODO
    """

    x_train, x_test = x
    y_train, y_test = y

    # capture only decision time points
    idx_train = np.nonzero(y_train)
    idx_test  = np.nonzero(y_test)

    model = OneVsRestClassifier(RidgeClassifier(alpha=0.0, fit_intercept=False, **kwargs)).fit(x_train[idx_train], y_train[idx_train])
    score = model.score(x_test[idx_test], y_test[idx_test])

    # # confusion matrix
    # ConfusionMatrixDisplay.from_predictions(y_test[idx_test], model.predict(x_test[idx_test]))
    # plt.show()
    # plt.close()

    # with np.errstate(divide='ignore', invalid='ignore'):
    #     cm = metrics.confusion_matrix(y_test[idx_test], model.predict(x_test[idx_test]))
    #     score = np.sum(np.diagonal(cm))/np.sum(cm)  # turned out to be equivalent to the native sklearn score

    return score


def multiOutputClassification(x, y, **kwargs):
    """
    Multiple output (binary and multi-class) classification tasks
    #TODO
    """

    x_train, x_test = x
    y_train, y_test = y

    model = MultiOutputClassifier(RidgeClassifier(alpha=0.5, fit_intercept=True, **kwargs)).fit(x_train, y_train)
    score = model.score(x_test, y_test)    
    
    return score


def select_model(y):
    """
    Select the right model depending on the nature of the target
    variable
    #TODO
    """
    
    if y.dtype in [np.float32, np.float64]:
        if y.ndim == 1:
            return regression # regression 
        else:
            return multiOutputRegression # multilabel regression

    elif y.dtype in [np.int32, np.int64]:
        if y.ndim == 1:
            if len(np.unique(y)) == 2: # binary classification
                return classification
            else:
                return multiClassClassification # multiclass classification
        else:
            return multiOutputClassification # multilabel and/or multiclass classification
    

def run_task(reservoir_states, target, **kwargs):
    """
    #TODO
    Function that calls the method to run the task specified by 'task'

    Parameters
    ----------
    task : {'regression', 'classification'}
    reservoir_states : tuple of numpy.ndarrays
        simulated reservoir states for training and test; the shape of each
        numpy.ndarray is n_samples, n_reservoir_nodes
    target : tuple of numpy.ndarrays
        training and test targets or output labels; the shape of each
        numpy.ndarray is n_samples, n_labels
    kwargs : other keyword arguments are passed to one of the following
        functions:
            memory_capacity_task(); delays=None, t_on=0
            pattern_recognition_task(); pttn_lens

    Returns
    -------
    df_res : pandas.DataFrame
        data frame with task scores
    """

    # print('\n PERFORMING TASK ...')

    # verify dimensions of x and y
    x_train, x_test, y_train, y_test = check_xy_dims(x=reservoir_states, y=target)

    # select training model 
    func = select_model(y=y_train)

    score = func(x=(x_train, x_test), y=(y_train, y_test), **kwargs)
    print(f'\t\t score = {score}')

    df_res = pd.DataFrame(data=[score],
                          columns=['score'])

    return df_res
