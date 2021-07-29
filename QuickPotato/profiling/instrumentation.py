from time import time
import cProfile
import pstats


class Profiler(object):

    def __init__(self):

        self.functional_output = None
        self.total_response_time = None
        self.performance_statistics = None

    def profile_method_under_test(self, method, *args, **kwargs):
        """

        Returns
        -------

        """
        # Initializing the Profiler, ProfileResults and creating the results
        profiler = cProfile.Profile()

        # Start Profiling the method

        # TODO: should this be time.perf_counter()?
        start_time = time()
        profiler.enable()
        self.functional_output = method(*args, **kwargs)
        profiler.disable()
        end_time = time()
        self.total_response_time = end_time - start_time

        # Dump performance statistical
        self.performance_statistics = pstats.Stats(profiler).stats
