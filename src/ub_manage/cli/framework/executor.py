import sys
import time
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Callable, Dict, List, Optional

from ub_manage.cli.framework.base import BaseCommand, CommandContext


class BaseExecutor:
    """
    Base command executor.

    Provides core functionality for executing commands with parameter validation,
    timeout support, and execution history tracking.
    """

    def __init__(self, context_factory: Callable = None, timeout: int = None, capture_output: bool = True):
        """
        Initialize the executor.

        Args:
            context_factory: Context factory function for creating CommandContext instances.
            timeout: Execution timeout in seconds (optional).
            capture_output: Whether to capture command output.
        """
        self.context_factory = context_factory or self._default_context_factory
        self.timeout = timeout
        self.capture_output = capture_output
        self.execution_history: List[Dict] = []

    def _default_context_factory(self, **kwargs) -> CommandContext:
        """
        Default context factory.

        Creates a CommandContext with the provided kwargs.

        Args:
            **kwargs: Keyword arguments passed to CommandContext constructor.

        Returns:
            CommandContext instance.
        """
        return CommandContext(**kwargs)

    def set_context_factory(self, factory: Callable) -> None:
        """
        Set the context factory.

        Args:
            factory: Callable that creates CommandContext instances.
        """
        self.context_factory = factory

    def execute(self, command: BaseCommand, params: Dict[str, Any]) -> int:
        """
        Execute a command.

        Executes the given command with the provided parameters, handling
        context creation, parameter validation, and execution time tracking.

        Args:
            command: Command instance to execute.
            params: Dictionary of parameter names to values.

        Returns:
            Exit code: 0 for success, non-zero for failure.

        Examples:
            >>> executor = BaseExecutor()
            >>> exit_code = executor.execute(command, {'param1': 'value1'})
        """
        start_time = time.time()

        try:
            context = self.context_factory(params=params)

            if isinstance(command, BaseCommand):
                validation_result = command.validate_parameters(params)
                if not validation_result:
                    print("Parameter validation failed:", file=sys.stderr)
                    for error in validation_result.errors:
                        print(f"  - {error}", file=sys.stderr)
                    return 1

            if self.timeout:
                return self._execute_with_timeout(command, context)
            else:
                return self._execute_direct(command, context)

        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            return 1

        finally:
            execution_time = time.time() - start_time
            self.execution_history.append(
                {
                    'command': command.get_name(),
                    'params': params,
                    'execution_time': execution_time,
                    'timestamp': time.time(),
                }
            )

    def _execute_direct(self, command: BaseCommand, context: CommandContext) -> int:
        """
        Execute command directly without timeout.

        Args:
            command: Command instance to execute.
            context: Execution context.

        Returns:
            Exit code from command execution.
        """
        return command.execute(context)

    def _execute_with_timeout(self, command: BaseCommand, context: CommandContext) -> int:
        """
        Execute command with timeout.

        Runs the command in a separate thread and returns after timeout if
        the command hasn't completed.

        Args:
            command: Command instance to execute.
            context: Execution context.

        Returns:
            Exit code: 0 for success, 124 for timeout, other values for errors.
        """
        result_queue = Queue(maxsize=1)
        stop_event = Event()

        def worker():
            try:
                result = command.execute(context)
                result_queue.put(result)
            except Exception as e:
                result_queue.put((1, str(e)))

        thread = Thread(target=worker)
        thread.daemon = True
        thread.start()

        try:
            thread.join(self.timeout)

            if thread.is_alive():
                print(f"Command execution timed out ({self.timeout} seconds)", file=sys.stderr)
                return 124
            try:
                result = result_queue.get_nowait()
                if isinstance(result, tuple):
                    return result[0]
                return result
            except Empty:
                return 1

        except KeyboardInterrupt:
            print("\nCommand interrupted by user", file=sys.stderr)
            return 130

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns execution history statistics including total executions,
        total time, and average execution time.

        Returns:
            Dictionary of execution statistics.
        """
        if not self.execution_history:
            return {}

        total_executions = len(self.execution_history)
        total_time = sum(h['execution_time'] for h in self.execution_history)

        return {
            'total_executions': total_executions,
            'total_time': total_time,
            'avg_time': total_time / total_executions if total_executions > 0 else 0,
        }


class AsyncExecutor(BaseExecutor):
    """
    Asynchronous command executor.

    Extends BaseExecutor to support asynchronous command execution
    with task queuing and result retrieval.
    """

    def __init__(
        self, context_factory: Callable = None, timeout: int = None, capture_output: bool = True, max_workers: int = 4
    ):
        """
        Initialize the asynchronous executor.

        Args:
            context_factory: Context factory function for creating CommandContext instances.
            timeout: Execution timeout in seconds (optional).
            capture_output: Whether to capture command output.
            max_workers: Maximum number of worker threads.
        """
        super().__init__(context_factory, timeout, capture_output)
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.results = {}

    def execute_async(self, command: BaseCommand, params: Dict[str, Any], task_id: str = None) -> str:
        """
        Execute a command asynchronously.

        Adds the command to the task queue for asynchronous execution.

        Args:
            command: Command instance to execute.
            params: Dictionary of parameter names to values.
            task_id: Optional task ID. If not provided, a unique ID will be generated.

        Returns:
            Task ID string for retrieving results later.

        Examples:
            >>> task_id = executor.execute_async(command, {'param1': 'value1'})
            >>> print(f"Task queued with ID: {task_id}")
        """
        if task_id is None:
            task_id = f"task_{len(self.results) + 1}"

        self.task_queue.put({'task_id': task_id, 'command': command, 'params': params})

        return task_id

    def get_result(self, task_id: str) -> Optional[Dict]:
        """
        Get the result of an asynchronous task.

        Args:
            task_id: Task ID returned from execute_async.

        Returns:
            Dictionary containing task results if available, None otherwise.
        """
        return self.results.get(task_id)

    def wait_all(self) -> None:
        """
        Wait for all queued tasks to complete.

        Blocks until all tasks in the queue have been processed.
        """
        self.task_queue.join()
