"""
TODO: module-level docstring
"""

# standard library
import random
import string
from functools import wraps, partial
from typing import Callable, Optional, Set

# QuickPotato
from QuickPotato import performance_test
from QuickPotato.configuration.management import options
from QuickPotato.profiling.observer import Subject, Observer
from QuickPotato.profiling.instrumentation import Profiler
from QuickPotato.utilities.exceptions import CouchPotatoCannotFindMethod


# -----------------------------------------------------------------------------
# DECORATORS
# -----------------------------------------------------------------------------
class PerformanceBreakpoint(Subject):

    _observers: Set[Observer] = set()

    def __init__(
        self,
        enabled: bool = True,
        database_name: str = performance_test.test_case_name,
        test_id: str = performance_test.current_test_id,
        execution_wrapper: Optional[Callable] = None,
        observers: Optional = None,
    ) -> None:
        """
        """
        self.enabled: bool = enabled
        self.database_name: str = database_name
        self.test_id: str = test_id
        self.execution_wrapper: Optional[Callable] = execution_wrapper
        if observers:
            for observer in observers:
                self.attach(observer)

    def __call__(
        self,
        function: Callable,
    ) -> Callable:
        """
        TODO: ensure the decorator works when no arguments are provided
        """
        @wraps(function)
        def execute_function(*args, **kwargs):
            if (
                self.enabled
                and options.enable_intrusive_profiling
            ):
                self.sample_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                self.profiler = Profiler()

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

        self.function: Optional[Callable] = function

        if self.function is None:
            return partial(PerformanceBreakpoint, enabled=self.enabled)

        elif not callable(self.function):
            raise CouchPotatoCannotFindMethod()

        return execute_function

    def attach(self, observer: Observer) -> None:
        self._observers.add(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)
