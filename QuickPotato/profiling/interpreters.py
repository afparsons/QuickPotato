"""
TODO: consider renaming "interpreters" to "listeners" or "handlers"
"""

# standard library
import asyncio
from datetime import datetime
from functools import partial
from abc import abstractmethod
from typing import Generator, Dict, Union, Tuple

# QuickPotato
from QuickPotato.database.queries import Crud
from QuickPotato.profiling.observer import Observer
from QuickPotato.configuration.management import options


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class Interpreter(Observer):
    """
    """

    def __init__(
        self,
        method_name: str,
        test_case_name: str,
        database_name: str,
    ) -> None:
        """
        """
        self.database_name = database_name
        self.test_case_name = test_case_name
        self.method_name = method_name

    @classmethod
    def update(cls, subject) -> None:
        """
        TODO: PROBLEM! Check how to properly scope cls._instance.
            At the moment, any Interpreter subclass acts as a singleton.
            For example:

            >>> @PerformanceBreakpoint(observers=[SimpleInterpreter])
            ...    def function_1()
            ...        ...

            >>> @PerformanceBreakpoint(observers=[SimpleInterpreter])
            ...     def function_2()
            ...         ...

            >>> function_1()
            # correct
            self.method_name='function_1'

            >>> function_2()
            # incorrect
            self.method_name='function_1'
        """
        if cls._instance is None:
            cls._instance = cls(
                method_name=subject.function.__name__,
                database_name=subject.database_name,
                test_case_name=subject.test_case_name,
            )
            cls._instance._update(subject)
        else:
            cls._instance._update(subject)

    @abstractmethod
    def _update(self, subject) -> None:
        raise NotImplemented


class SimpleInterpreter(Interpreter):

    def _update(self, subject) -> None:
        """
        Simply prints information stored by the PerformanceBreakpoint decorator
        and the total response time from the subject's profiler.
        """
        self.test_id = subject.test_id
        self.sample_id: str = subject.sample_id

        print(f'{self.__class__.__name__}')
        print(f' ├─ {self.method_name=}')
        print(f' ├─ {self.test_id=}')
        print(f' ├─ {self.sample_id=}')
        print(f' ├─ {self.database_name=}')
        print(f' ├─ {subject.profiler.total_response_time=}')


class StatisticsInterpreter(Crud, Interpreter):

    def _update(self, subject) -> None:
        """
        """
        self.test_id = subject.test_id
        self.sample_id: str = subject.sample_id
        self.performance_statistics: Dict = subject.profiler.performance_statistics
        self.total_response_time: float = subject.profiler.total_response_time

        if options.enable_asynchronous_payload_delivery:
            self.upload_payload_to_database_async()
        else:
            self.upload_payload_to_database_sync()

    def __init__(
        self,
        method_name: str,
        database_name: str,
        test_case_name: str,
    ) -> None:

        Crud.__init__(self)
        Interpreter.__init__(
            self,
            method_name=method_name,
            database_name=database_name,
            test_case_name=test_case_name
        )

        self.using_server_less_database = bool(self._validate_connection_url(database_name)[0:6] == "sqlite")
        self.epoch_timestamp = datetime.now().timestamp()
        self.human_timestamp = datetime.now()

    def build_payload(self) -> Tuple[Dict[str, Union[str, int, float]]]:
        """
        """
        return *self.iterate_through_profiled_stack(),

    def upload_payload_to_database_async(self) -> None:
        """
        Returns
        -------

        """
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor=None, func=self.send_payload_to_database)

    def upload_payload_to_database_sync(self) -> None:
        """
        Returns
        -------

        """
        self.send_payload_to_database()

    def send_payload_to_database(self) -> None:
        """
        :return:
        """
        payload: Tuple[Dict[str, Union[str, int, float]]] = self.build_payload()
        # Dividing payload into multiple inserts to work around server-less variable restrictions
        len_payload: int = len(payload)
        if self.using_server_less_database and len_payload >= 999:
            for i in range(0, len_payload, 999):
                self.insert_performance_statistics(
                    payload=[payload[i:i+999]],
                    database=self.database_name
                )
        else:
            # Inserting full payload into server-based database
            self.insert_performance_statistics(
                payload=payload,
                database=self.database_name
            )

    def iterate_through_profiled_stack(
        self,
    ) -> Generator[Dict[str, Union[str, int, float]], None, None]:
        """

        :return:
        """
        for function, (cc, nc, tt, ct, callers) in self.performance_statistics.items():

            child_path = function[0]
            child_line_number = function[1]
            child_function_name = function[2]

            if len(callers) == 0:
                if str(function[2]) == self.method_name:
                    yield {
                        "test_id": self.test_id,
                        "sample_id": self.sample_id,
                        "test_case_name": self.test_case_name,
                        "name_of_method_under_test": self.method_name,
                        "epoch_timestamp": self.epoch_timestamp,
                        "human_timestamp": self.human_timestamp,
                        "child_path": child_path,
                        "child_line_number": child_line_number,
                        "child_function_name": child_function_name,
                        "parent_path": "~",
                        "parent_line_number": 0,
                        "parent_function_name": self.sample_id,
                        "number_of_calls": nc,
                        "total_time": tt,
                        "cumulative_time": ct,
                        "total_response_time": self.total_response_time
                    }
                else:
                    continue

            else:
                for row in callers:
                    yield {
                        "test_id": self.test_id,
                        "sample_id": self.sample_id,
                        "test_case_name": self.test_case_name,
                        "name_of_method_under_test": self.method_name,
                        "epoch_timestamp": self.epoch_timestamp,
                        "human_timestamp": self.human_timestamp,
                        "child_path": child_path,
                        "child_line_number": child_line_number,
                        "child_function_name": child_function_name,
                        "parent_path": row[0],
                        "parent_line_number": row[1],
                        "parent_function_name": row[2],
                        "number_of_calls": nc,
                        "total_time": tt,
                        "cumulative_time": ct,
                        "total_response_time": self.total_response_time
                    }
