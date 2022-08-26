""" Creates a random walk with the specified properties """

from typing import List, Optional

import numpy as np


def random_walk(total_length: int, dims: int, step_magnitude: float = 1.0, window_size: int = 1,
                interval: Optional[List[np.ndarray]] = None, distribution: str = 'uniform',
                order: float = 1.0) -> np.ndarray:
    """
    Creates a random walk with the specified properties. Can be used to simulate camera shaking or POI drift.
    steps ~ step_magnitude * U[-1,1]^order

    :param total_length: length of the random walk
    :param dims: In how many dimensions the random walk should happen
    :param step_magnitude: Maximum magnitude of any coordinate in a single step
    :param window_size: Convolve the final trajectory with an average filter that smoothens the trajectory with a
                        given filter size.
    :param interval: Constrain the random walk to an interval and mirror steps if they go beyond. List of arrays
                     with dimension dims.
    :param distribution: Distribution to sample steps from. Choose from ['normal', 'uniform'].
    :param order: Sample from higher order distribution instead of the uniform. Higher order leads to steps being
                  less frequently close to step_magnitude and thus overall decreased variance.
    :return: The random walk trajectory (total_length, dims)
    """
    # Set sampling distribution
    if distribution == 'uniform':
        dist_fun = np.random.rand
    elif distribution == 'normal':
        dist_fun = np.random.randn
    else:
        raise RuntimeError(f'Unknown distribution: {distribution}. Choose between "normal" and "uniform"')

        # Sample random steps
    random_steps = step_magnitude * np.random.choice([-1, 1], (total_length, dims)) * dist_fun(total_length,
                                                                                               dims) ** order

    # Cumulate the random steps to a random walk trajectory
    cumulative_steps = np.cumsum(random_steps, axis=0)

    # Keep the steps within the predefined interval
    if interval is not None:
        assert len(interval) == 2, "interval must have length of two"
        left_bound = np.array(interval[0])
        size = np.abs(interval[1] - left_bound)
        cumulative_steps = np.abs((cumulative_steps - left_bound + size) % (2 * size) - size) + left_bound

    # Smooth the random walk trajectory using a sliding window of size window_size
    if window_size > 1:
        initial_padding = np.ones((window_size - 1, dims)) * cumulative_steps[:1, :]
        cumulative_steps_padded = np.vstack((initial_padding, cumulative_steps))
        for i in range(dims):
            cumulative_steps[:, i] = np.convolve(cumulative_steps_padded[:, i], np.ones(window_size) / window_size,
                                                 'valid')

    return cumulative_steps
