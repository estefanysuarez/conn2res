# -*- coding: utf-8 -*-
"""
Connectome-informed reservoir - Echo-State Network
=======================================================================
This example demonstrates how to use the conn2res toolbox to implement
perform multiple tasks across dynamical regimes, and using different
types local dynamics
"""
import warnings

import os
os.environ['OPENBLAS_NUM_THREADS'] = "1"
os.environ['MKL_NUM_THREADS'] = "1"

import time
import multiprocessing as mp

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from conn2res import tasks
from conn2res.tasks import Conn2ResTask
from conn2res.connectivity import Conn
from conn2res.reservoir import EchoStateNetwork
from conn2res.readout import Readout
from conn2res import readout, plotting, utils

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=RuntimeWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# -----------------------------------------------------
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJ_DIR, 'connectomes')
OUTPUT_DIR = os.path.join(PROJ_DIR, 'results')
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# -----------------------------------------------------
N_PROCESS = 30
TASK = 'MemoryCapacity'
METRIC = ['corrcoef']
metric_kwargs = {
    'multioutput': 'sum',
    'nonnegative': 'absolute'
}
INPUT_GAIN = 0.0001
ALPHAS = np.linspace(0, 2, 41)[1:]


def run_workflow(w, x, y, input_nodes, output_nodes, rand=True, filename=None, **kwargs):

    conn = Conn(w=w)
    if rand:
        conn.randomize(swaps=10)
        # np.save(os.path.join(OUTPUT_DIR, f'{filename}.npy'), conn.w)

    conn.scale_and_normalize()

    w_in = np.zeros((1, conn.n_nodes))
    w_in[:, input_nodes] = np.eye(1)

    esn = EchoStateNetwork(w=conn.w, activation_function='tanh')
    readout_module = Readout(estimator=readout.select_model(y))

    x_train, x_test, y_train, y_test = readout.train_test_split(x, y)

    df_alpha = []
    for alpha in ALPHAS:

        print(f'\n\t\t\t----- alpha = {alpha} -----')

        esn.w = alpha * conn.w

        rs_train = esn.simulate(
            ext_input=x_train, w_in=w_in, input_gain=INPUT_GAIN,
            output_nodes=output_nodes
        )

        rs_test = esn.simulate(
            ext_input=x_test, w_in=w_in, input_gain=INPUT_GAIN,
            output_nodes=output_nodes
        )

        df_res = readout_module.run_task(
            X=(rs_train, rs_test), y=(y_train, y_test),
            sample_weight=None, metric=METRIC,
            readout_modules=None, readout_nodes=None,
            **metric_kwargs
        )

        df_res['alpha'] = np.round(alpha, 3)
        df_alpha.append(df_res)

    df_alpha = pd.concat(df_alpha, ignore_index=True)
    df_alpha = df_alpha[['alpha', METRIC[0]]]
    df_alpha.to_csv(
        os.path.join(OUTPUT_DIR, f'{filename}_scores.csv'),
        index=False
        )


def run_experiment(connectome, x, y):
    w = np.loadtxt(os.path.join(DATA_DIR, connectome, 'conn.csv'), delimiter=',', dtype=float)
    labels = pd.read_csv(os.path.join(DATA_DIR, connectome, 'labels.csv'))['Sensory'].values

    run_workflow(w.copy(), x, y,
        input_nodes=np.where(labels == 1)[0],
        output_nodes=np.where(labels == 0)[0],
        rand=False,
        filename=f'{connectome}_empirical')

    # run workflow for nulls
    params = []
    for i in range(500):
        params.append(
            {
                'w': w.copy(),
                'x': x,
                'y': y,
                'input_nodes': np.where(labels == 1)[0],
                'output_nodes': np.where(labels == 0)[0],
                'filename': f'{connectome}_null_{i}'
            }
        )

    print('\nINITIATING PROCESSING TIME')
    t0 = time.perf_counter()

    pool = mp.Pool(processes=N_PROCESS)
    res = [pool.apply_async(run_workflow, (), p) for p in params]
    for r in res: r.get()
    pool.close()

    print('\nTOTAL PROCESSING TIME')
    print(time.perf_counter()-t0, "seconds process time")
    print('END')


def main():

    task = Conn2ResTask(name=TASK)
    x, y = task.fetch_data(n_trials=4050)
    np.save(os.path.join(OUTPUT_DIR, 'input.npy'), x)
    np.save(os.path.join(OUTPUT_DIR, 'output.npy'), y)

    # x = np.load(os.path.join(OUTPUT_DIR, 'input.npy'))
    # y = np.load(os.path.join(OUTPUT_DIR, 'output.npy'))

    connectomes = [
        'celegans',
        'drosophila',
        'macaque_modha',
        'mouse',
        'rat'
    ]

    for connectome in connectomes:
        run_experiment(connectome, x, y)


if __name__ == '__main__':
    main()
