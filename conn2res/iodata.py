# -*- coding: utf-8 -*-
"""
Functions for generating input/output data for tasks

@author: Estefany Suarez
"""

import os
from re import I
import numpy as np
import neurogym as ngym
import matplotlib.pyplot as plt
import seaborn as sns

from .task import select_model

NEUROGYM_TASKS = [
                'AntiReach',
                # 'Bandit',
                'ContextDecisionMaking',
                # 'DawTwoStep',
                'DelayComparison',
                'DelayMatchCategory',
                'DelayMatchSample',
                'DelayMatchSampleDistractor1D',
                'DelayPairedAssociation',
                # 'Detection',  # TODO: Temporary removing until bug fixed
                'DualDelayMatchSample',
                # 'EconomicDecisionMaking',
                'GoNogo',
                # 'HierarchicalReasoning',
                'IntervalDiscrimination',
                'MotorTiming',
                'MultiSensoryIntegration',
                # 'Null',
                'OneTwoThreeGo',
                'PerceptualDecisionMaking',
                'PerceptualDecisionMakingDelayResponse',
                'PostDecisionWager',
                'ProbabilisticReasoning',
                'PulseDecisionMaking',
                'Reaching1D',
                'Reaching1DWithSelfDistraction',
                'ReachingDelayResponse',
                'ReadySetGo',
                'SingleContextDecisionMaking',
                'SpatialSuppressMotion',
                # 'ToneDetection'  # TODO: Temporary removing until bug fixed
            ]


NATIVE_TASKS = [
                'MemoryCapacity',
                # 'TemporalPatternRecognition'  
                ]


def get_available_tasks():
    return NEUROGYM_TASKS #+ NATIVE_TASKS


def unbatch(x):
    """
    Removes batch_size dimension from array

    Parameters
    ----------
    x : numpy.ndarray
        array with dimensions (seq_len, batch_size, features)

    Returns
    -------
    new_x : numpy.ndarray
        new array with dimensions (batch_size*seq_len, features)

    """
    #TODO right now it only works when x is (batch_first = False)
    return np.concatenate(x, axis=0)


def encode_labels(labels):
    """
        Binary encoding of categorical labels for classification 
        problems
        #TODO
    """

    enc_labels = -1 * np.ones((labels.shape[0], len(np.unique(labels))), dtype=np.int16)
    
    for i, label in enumerate(labels):
        enc_labels[i][label] = 1

    return enc_labels


def fetch_dataset(task, n_trials=100, *args, **kwargs):
    """
    Fetches inputs and labels for 'task' from the NeuroGym 
    repository

    Parameters
    ----------
    task : {'AntiReach', 'Bandit', 'ContextDecisionMaking', 
    'DawTwoStep', 'DelayComparison', 'DelayMatchCategory',
    'DelayMatchSample', 'DelayMatchSampleDistractor1D',
    'DelayPairedAssociation', 'Detection', 'DualDelayMatchSample',
    'EconomicDecisionMaking', 'GoNogo', 'HierarchicalReasoning',
    'IntervalDiscrimination', 'MotorTiming', 'MultiSensoryIntegration',
    'OneTwoThreeGo', 'PerceptualDecisionMaking',
    'PerceptualDecisionMakingDelayResponse', 'PostDecisionWager',
    'ProbabilisticReasoning', 'PulseDecisionMaking',
    'Reaching1D', 'Reaching1DWithSelfDistraction',
    'ReachingDelayResponse', 'ReadySetGo',
    'SingleContextDecisionMaking', 'SpatialSuppressMotion',
    'ToneDetection'}
    Task to be performed
    
    unbatch_data : bool, optional
        If True, it adds an extra dimension to inputs and labels 
        that corresponds to the batch_size. Otherwise, it returns an
        observations by features array for the inputs, and a one
        dimensional array for the labels.

    Returns
    -------
    inputs : numpy.ndarray
        array of observations by features
    labels : numpy.ndarray
        unidimensional array of labels 
    """

    if task in NEUROGYM_TASKS:

        # create a Dataset object from NeuroGym
        kwargs = {'dt': 100}
        dataset = ngym.Dataset(task+'-v0', env_kwargs=kwargs)

        # get environment object 
        env = dataset.env

        # generate per trial dataset
        _ = env.reset()
        inputs = []
        labels = []
        for trial in range(n_trials):
            env.new_trial()
            ob, gt = env.ob, env.gt

            # store input
            inputs.append(ob)

            # store labels
            if gt.ndim == 1: labels.append(gt[:, np.newaxis])
            else: labels.append(gt)

    elif task in NATIVE_TASKS:
        # create a native conn2res Dataset 
        inputs, labels = create_nativet_dataset(task, **kwargs)

    return inputs, labels


def create_nativet_dataset(task, tau_max=20, **kwargs):

    if task == 'MemoryCapacity':
        x = np.random.uniform(-1, 1, (1000+tau_max))[:,np.newaxis]
        y = np.hstack([x[tau_max-tau:-tau] for tau in range(1,tau_max+1)])
    
    return x, y


def split_dataset(data, frac_train=0.7):

    """
    Splits data into training and test sets according to
    'frac_train'

    Parameters
    ----------
    data : numpy.ndarray
        data array to be split
    frac_train : float, from 0 to 1
        fraction of samples in training set

    Returns
    -------
    training_set : numpy.ndarray
        array with training observations
    test_set     : numpy.ndarray
        array with test observations
    """

    n_train = int(frac_train * len(data))

    if isinstance(data, list):
        return np.vstack(data[:n_train]), np.vstack(data[n_train:])
    else:
        return data[:n_train], data[n_train:]


def visualize_data(task, x, y, plot=True):
    """
    #TODO
    Visualizes dataset for task

    Parameters
    ----------
    task : str
    x,y  : list or numpy.ndarray
        
    """

    print(f'\n----- {task.upper()} -----')
    print(f'\tNumber of trials = {len(x)}')

    # convert x and y to arrays for visualization
    if isinstance(x, list): x = np.vstack(x[:5])
    if isinstance(y, list): y = np.vstack(y[:5]).squeeze()

    print(f'\tinputs shape = {x.shape}')
    print(f'\tlabels shape = {y.shape}')

    # number of features, labels and classes 
    try: n_features = x.shape[1]
    except: n_features = 1

    try: n_labels = y.shape[1]
    except: n_labels = 1
    n_classes = len(np.unique(y))

    model = select_model(y)
    
    print(f'\t  n_features = {n_features}')
    print(f'\tn_labels   = {n_labels}')
    print(f'\tn_classes  = {n_classes}')
    print(f'\tlabel type : {y.dtype}')
    print(f'\tmodel = {model.__name__}')

    if plot:
        fig = plt.figure(num=1, figsize=(12,10))
        ax = plt.subplot(111)

        x_labels  = [f'I{n+1}' for n in range(n_features)]
        y_labels = [f'O{n+1}' for n in range(n_labels)]

        plt.plot(x[:], label=x_labels)
        plt.plot(y[:], label=y_labels)
        plt.legend()
        plt.suptitle(task)
        
        sns.despine(offset=10, trim=True)
        # fig.savefig(fname=f'figs/{task}_io.png', transparent=True, bbox_inches='tight', dpi=300)
        plt.show()
        plt.close()
    

