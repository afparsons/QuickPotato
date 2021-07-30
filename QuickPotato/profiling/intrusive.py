"""
Defines intrusive profiling decorators.

Intrusive profiling decorators wrap callable definitions (functions or methods)
and explicitly profile that callable's execution.
"""

# standard library
import random
import string
from functools import wraps, partial
from typing import Callable, Optional, Set, Type

# QuickPotato
from QuickPotato import performance_test
from QuickPotato.configuration.management import options
from QuickPotato.profiling.instrumentation import Profiler
from QuickPotato.profiling.observer import Observer, Subject
from QuickPotato.utilities.exceptions import CouchPotatoCannotFindMethod


# -----------------------------------------------------------------------------
# DECORATORS
# -----------------------------------------------------------------------------
class PerformanceBreakpoint(Subject):
    """
    TODO: properly document this decorator in general and observers in particular
    """
    def __new__(
        cls,
        function: Optional[Callable] = None,
        *args,
        **kwargs,
    ):
        """
        """
        self = super().__new__(cls)
        self.__init__(*args, **kwargs)
        if not function:
            return self
        return self.__call__(function)

    def __init__(
        self,
        enabled: bool = True,
        execution_wrapper: Optional[Callable] = None,
        observers: Optional = None,
        database_name: Optional[str] = None,
        test_case_name: Optional[str] = None,
        test_id: Optional[str] = None,
    ) -> None:
        """
        TODO: `observers` should be Optional[Iterable] or something analogous
        """
        self.enabled: bool = enabled
        self._database_name: str = database_name
        self._test_case_name: str = test_case_name
        self._test_id: str = test_id

        self.execution_wrapper: Optional[Callable] = execution_wrapper
        self._observers: Set[Type[Observer]] = set()
        if observers:
            for observer in observers:
                self.attach(observer)

    def __call__(
        self,
        function: Callable = None,
    ) -> Callable:
        """
        """
        @wraps(function)
        def execute_function(*args, **kwargs):
            """
            """
            self.test_id = self._test_id or performance_test.current_test_id
            self.test_case_name = self._test_case_name or performance_test.test_case_name
            self.database_name = self._database_name or performance_test.database_name

            # print(f'{performance_test.__dict__["current_test_id"]=}')
            # print(f'exec: {self}')
            # print(f'  ...  {self.test_id=}')
            # print(f'  ...  {self.database_name=}')
            # print(f'  ...  {self._observers=}')
            # print(f'  ...  {function=}')
            # print()

            if self.enabled and options.enable_intrusive_profiling:
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

    def attach(self, observer: Type[Observer]) -> None:
        self._observers.add(observer)

    def detach(self, observer: Type[Observer]) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        """
        Broadcasts a reference of this instance to all attached observers.
        Each observer must implement an `update(self, subject)` method.
        """
        try:
            for observer in self._observers:
                observer.update(self)
        except AttributeError as attribute_error:
            raise AttributeError(
                'Observers must implement an `update(self, subject)` method'
            ) from attribute_error
