import logging
import abc
import time

from .func_runner import FuncRunner

LOGGER = logging.getLogger(__name__)


class Loom(abc.ABC):
    """ Loom class """

    def __init__(self, max_runner_cap, sleep_time=.1):
        """ Base Loom Initializer

        Args:
            max_runner_cap (int): The total number of runners that are allowed to be running at any
                                  given time.
            sleep_time (int): The amount of time to sleep between checks to get the total number
                              of active runners.
        """

        self.max_runner_cap = max_runner_cap
        self.sleep_time = sleep_time
        self.runners = list()

    @abc.abstractmethod
    def add_runner(self, runner, key):
        """ this method is overridden in child classes """

        pass

    def add_function(self, func, args=None, kwargs=None, key=None):
        """ Adds function in the Loom

        Args:
            func (reference): reference to the function
            args (list): function args
            kwargs (dict): function kwargs
            key (str): ket to store the function output in dictionary
        """

        if args is None:
            args = list()
        if kwargs is None:
            kwargs = dict()

        if key is None:
            key = len(self.runners)
        fr = FuncRunner(func, *args, **kwargs)
        self.add_runner(fr, key)

    def add_func(self, func, *args, **kwargs):
        """ Adds function in the Loom

        Args:
            func (reference): function reference
            *args: function args
            **kwargs: function kwargs
        """

        key = kwargs.pop('key', None)
        self.add_function(func, args, kwargs, key=key)

    def add_work(self, workload):
        """ Adds work to the loom

        Args:
            workload (list): list of works [(func, args, kwargs, key), (func2, args2, kwargs2), ...]
        """

        for work in workload:
            # Allow an optional key in the workload
            # e.g.:  [(func, args, kwargs, key), (func2, args2, kwargs2), ...]
            if len(work) > 4 or len(work) == 0:
                raise ValueError('Need 1 to 4 values to unpack')

            key = work[3] if len(work) == 4 else None
            kwargs = work[2] if len(work) > 2 else None
            args = work[1] if len(work) > 1 else None
            self.add_function(work[0], args, kwargs, key=key)

    def execute(self):
        """ Executes runners and returns output dict """

        started = list()
        for runner in self.runners:
            runner.start()
            started.append(runner)
            while self.get_active_runner_count() >= self.max_runner_cap:
                time.sleep(self.sleep_time)
        for started_runner in started:
            started_runner.join()

        return self.get_output()

    def get_active_runner_count(self):
        """ Returns the total number of runners running at the present time """

        count = 0
        for runner in self.runners:
            if runner.is_running():
                count += 1
        return count

    def get_output(self):
        """ Returns dictionary of tracker dictionaries containing runner output, error,
        started time, finished time and execution time of the given runner.
        runner key or the order in which function was added is the key to get the tracker
        dictionary

        Returns:
            dict: output dict
            Examples:
                {
                    "runner1 key/order" : {
                            "output": runner output,
                            "error": runner errors,
                            "started_time": datetime.now() time stamp when runner was started
                            "finished_time": datetime.now() time stamp when runner was completed,
                            "execution_time: total execution time in seconds",
                            "got_error": boolean
                        },
                    "runner2 key/order" : {
                            "output": runner output,
                            "error": runner errors,
                            "started_time": datetime.now() time stamp when runner was started
                            "finished_time": datetime.now() time stamp when runner completed,
                            "execution_time: total execution time in seconds",
                            "got_error": boolean
                        }
                }
        """

        output_dict = dict()
        for runner in self.runners:
            output_dict[runner.key] = dict(runner.tracker)
        return output_dict
