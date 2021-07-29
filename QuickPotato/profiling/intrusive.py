import random
import string
from functools import wraps, partial, update_wrapper
from QuickPotato import performance_test
from QuickPotato.configuration.management import options
from QuickPotato.profiling.instrumentation import Profiler
# from QuickPotato.profiling.interpreters import StatisticsInterpreter
from QuickPotato.utilities.exceptions import CouchPotatoCannotFindMethod

from typing import *
from .observer import Subject, Observer


class PerformanceBreakpoint(Subject):

    _observers: Set[Observer] = set()

    def __init__(
        self,
        function: Callable,
        enabled: bool = True,
        execution_wrapper: Optional[Callable] = None,
        *observers
    ):
        """
        """
        update_wrapper(self, function)
        self.function: Callable = function
        self.enabled: bool = enabled
        self.execution_wrapper: Optional[Callable] = execution_wrapper
        for observer in observers:
            self.attach(observer)

    def __call__(
        self,
        *args,
        **kwargs
    ):
        """
        """
        if self.function is None:
            return partial(PerformanceBreakpoint, enabled=self.enabled)

        elif not callable(self.function):
            raise CouchPotatoCannotFindMethod()

        if (
            self.enabled
            and options.enable_intrusive_profiling
        ):
            self.sample_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.profiler: Profiler = Profiler()

            if self.execution_wrapper:
                self.profiler.profile_method_under_test(
                    self.execution_wrapper,
                    partial(self.function, *args, **kwargs)
                )
            else:
                self.profiler.profile_method_under_test(self.function, *args, **kwargs)

            self.notify()
            return self.profiler.functional_output
        else:
            return self.function(*args, **kwargs)

    def attach(self, observer: Observer) -> None:
        self._observers.add(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)


def performance_breakpoint(method=None, enabled=True):
    """
    This decorator can be used to gather performance statistical
    on a method.
    :param method: The method that is being profiled
    :param enabled: If True will profile the method under test
    :return: The method output
    """
    # ---------------------------------------------------------------------

    @wraps(method)
    def method_execution(*args, **kwargs):
        """
        An inner function that Will execute the method under test and enable the profiler.
        It will work together with the Results class to formulate a list containing dictionary
        that will store all metrics in a database or csv file.
        :param args: The Arguments of the method under test
        :param kwargs: The key word arguments of the method under test
        :return: the methods results
        """
        if enabled and options.enable_intrusive_profiling:

            sample_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            pf = Profiler()
            pf.profile_method_under_test(method, *args, **kwargs)

            StatisticsInterpreter(
                performance_statistics=pf.performance_statistics,
                total_response_time=pf.total_response_time,
                database_name=performance_test.test_case_name,
                test_id=performance_test.current_test_id,
                method_name=method.__name__,
                sample_id=sample_id
            )

            return pf.functional_output

        else:
            return method(*args, **kwargs)

    # ---------------------------------------------------------------------

    if method is None:
        return partial(performance_breakpoint, enabled=enabled)

    elif callable(method) is not True:
        raise CouchPotatoCannotFindMethod()

    else:
        # Execute the method under test
        output = method_execution

        return output
