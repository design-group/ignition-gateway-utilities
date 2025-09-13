"""
General.Multithreading

This module contains functions for multithreading in Ignition.
"""

import traceback
from ast import literal_eval
from java.lang import Thread
from java.lang import Runnable
from java.lang import Exception as JavaException
from java.util.concurrent import Executors
from java.util.concurrent import ThreadFactory
from java.util.concurrent import TimeUnit
from java.util.concurrent import ConcurrentHashMap

from com.inductiveautomation.ignition.common.script import ScriptContext
from com.inductiveautomation.ignition.common.execution import TPC

LOGGER = system.util.getLogger("General.Multithreading")
MULTITHREADING_SYSTEM_NAME = "Multithreading"


class MultiThreadTimeoutError(Exception):
	""" Indicates that a multithreaded operation has timed out."""

	def __init__(self, message="Multithreaded operation timed out"):
		self.message = message
		LOGGER.error(self.message)
		super(MultiThreadTimeoutError, self).__init__(self.message)


class FunctionWrapper(Runnable):
	"""
	DESCRIPTION: A java.lang.Runnable that will wrap around functions to execute them in a thread.
	"""

	def __init__(self, func, kwargs=None):
		"""
		DESCRIPTION: This function initializes the FunctionWrapper class
		"""
		self.kwargs = {} if not kwargs else kwargs
		self.func = func
		function_name = General.Utilities.get_function_qualified_path(func)
		kwargs_text = ', '.join(['{}={!r}'.format(k, v) for k, v in self.kwargs.items()])
		ScriptContext.setDescription("Asynchronous execution of: %s%s" % (function_name, kwargs_text))

	def run(self):
		"""
		DESCRIPTION: This function overrides the run() function of the threading.Thread class, to execute the function with kwargs
		"""
		self.func(**self.kwargs)


class ResultCapturingWrapper(Runnable):
	"""
	DESCRIPTION: A java.lang.Runnable that captures function results in a thread-safe map.
	"""

	def __init__(self, func, index, results_map, args=None, kwargs=None):
		"""
		DESCRIPTION: This function initializes the ResultCapturingWrapper class
		"""
		self.func = func
		self.index = index
		self.results_map = results_map
		self.args = args if args is not None else ()
		self.kwargs = kwargs if kwargs is not None else {}

		function_name = General.Utilities.get_function_qualified_path(func)
		if kwargs:
			kwargs_text = ', '.join(['{}={!r}'.format(k, v) for k, v in kwargs.items()])
			description = "Asynchronous execution of: %s(%s)" % (function_name, kwargs_text)
		elif args:
			args_text = ', '.join(['{!r}'.format(arg) for arg in args])
			description = "Asynchronous execution of: %s(%s)" % (function_name, args_text)
		else:
			description = "Asynchronous execution of: %s()" % function_name
		ScriptContext.setDescription(description)

	def run(self):
		"""
		DESCRIPTION: This function executes the function and stores the result
		"""
		try:
			if self.kwargs:
				result = self.func(**self.kwargs)
			elif self.args:
				result = self.func(*self.args)
			else:
				result = self.func()
			self.results_map.put(self.index, result)
		except (Exception, JavaException) as e:
			# Capture the full traceback for debugging
			LOGGER.warn("Exception in thread %d: %s" % (self.index, traceback.format_exc()))
			error_with_traceback = {'exception': e, 'traceback': traceback.format_exc(), 'thread_index': self.index}
			self.results_map.put(self.index, error_with_traceback)
			# Don't re-raise - we've captured the error for processing in the main thread


class AsyncThreadFactory(ThreadFactory):
	"""
	DESCRIPTION: A java.util.concurrent.ThreadFactory that will create threads with a name.
	"""

	def __init__(self, name, exception_handler):
		self.name = name
		self.exception_handler = exception_handler
		self.thread_factory = TPC.newThreadFactory(self.name, MULTITHREADING_SYSTEM_NAME)

	#NOTE: This is a java function, so we have to ignore the invalid name
	def newThread(self, runnable):  # pylint: disable=invalid-name
		"""
		DESCRIPTION: Creates the new thread, and customizes it to properly bubble back up to Ignition.
		"""
		thread = self.thread_factory.newThread(runnable)
		thread.setName(self.name)
		thread.setUncaughtExceptionHandler(self.exception_handler)
		return thread


class MultiThreadedException(Exception):
	"""
	DESCRIPTION: This exception will take a list of exceptions, and will print them all out when raised.
	PARAMETERS: exceptions (REQ, list[Exception]) - A list of exceptions that were raised
	"""

	def __init__(self, exceptions):
		"""
		DESCRIPTION: This function initializes the MultiThreadedException class
		PARAMETERS: exceptions (REQ, list[(str, Exception)]) - A list of names and exception tuples that were raised per thread
		"""
		self.exceptions = exceptions
		if len(self.exceptions) > 1:
			self.message = "Multiple exceptions were raised while multithreading"
		else:
			self.message = "An exception was raised while multithreading"

		super(MultiThreadedException, self).__init__(self.message)

	def __str__(self):
		"""
		DESCRIPTION: This function overrides the str() function to print out the exceptions
		"""
		return "%s: %s" % (self.message, self.exceptions)


class ThreadExecutionException(Exception):
	"""
	DESCRIPTION: Exception that preserves original traceback from thread execution
	"""

	def __init__(self, original_exception, thread_traceback, thread_index):
		self.original_exception = original_exception
		self.thread_traceback = thread_traceback
		self.thread_index = thread_index

		# Create a comprehensive error message
		message = "Exception in thread %d: %s\n\nOriginal traceback:\n%s" % (
			thread_index, str(original_exception), thread_traceback
		)
		super(ThreadExecutionException, self).__init__(message)

	def __str__(self):
		return "Exception in thread %d: %s\n\nOriginal traceback:\n%s" % (
			self.thread_index, str(self.original_exception), self.thread_traceback
		)


def wait_for_async_execution(func, kwargs_list=None, args_list=None, max_threads=-1, timeout_seconds=10):
	"""
	DESCRIPTION: Executes the function func asynchronously with the parameters and returns all results
	PARAMETERS: func (REQ, function) - The function to be executed
				kwargs_list (OPT, list) - A list of dictionaries with keyword arguments to be passed to the function
				args_list (OPT, list) - A list of tuples/lists with positional arguments to be passed to the function
				max_threads (OPT, int) - The maximum number of threads to be used.
										 If -1, it will just execute with as many threads as it can
				timeout_seconds (OPT, int) - The maximum number of seconds to wait for the threads to finish
	RETURNS: list - Results from all function executions in the same order as input parameters
	"""

	#NOTE: If our function showed up as a name, we would have to use the following line to get the actual function
	if not callable(func):
		if General.Utilities.is_valid_variable_name(func):
			func = literal_eval(func)

	# Determine which parameter list to use and validate input
	if kwargs_list is not None and args_list is not None:
		raise ValueError("Cannot specify both kwargs_list and args_list. Choose one.")
	elif kwargs_list is not None:
		param_list = kwargs_list
		use_kwargs = True
	elif args_list is not None:
		param_list = args_list
		use_kwargs = False
	else:
		# If no parameters provided, execute function once with no arguments
		param_list = [None]
		use_kwargs = True

	#NOTE: If the number of threads is -1, we will use the number of parameter options provided
	if max_threads == -1:
		max_threads = len(param_list)

	#NOTE: Define containers for exceptions and results
	exceptions = []
	# Use Java ConcurrentHashMap for thread-safe result storage
	results_map = ConcurrentHashMap()

	class AsyncExceptionHandler(Thread.UncaughtExceptionHandler):
		""" Handles uncaught exceptions in threads using the native Java UncaughtExceptionHandler interface."""

		#NOTE: This is a java function, so we have to ignore the invalid name
		def uncaughtException(self, thread, exception):  # pylint: disable=invalid-name
			# Capture more detailed exception information
			exception_info = {
				'thread': thread,
				'exception': exception,
				'thread_name': thread.getName(),
				'traceback': traceback.format_exc()
			}
			exceptions.append(exception_info)
			LOGGER.error("Uncaught exception in thread %s: %s" % (thread.getName(), traceback.format_exc()))

	function_name = General.Utilities.get_function_qualified_path(func)
	#NOTE: Execute the function in parallel with at most the number of threads in the pool,
	#NOTE: and wait for all of them to finish
	executor = Executors.newFixedThreadPool(max_threads, AsyncThreadFactory(function_name, AsyncExceptionHandler()))

	# Submit all tasks with their respective parameters
	for i in range(len(param_list)):
		if use_kwargs:
			wrapper = ResultCapturingWrapper(func, i, results_map, kwargs=param_list[i])
		else:
			wrapper = ResultCapturingWrapper(func, i, results_map, args=param_list[i])

		executor.execute(wrapper)

	executor.shutdown()
	finished_in_time = executor.awaitTermination(timeout_seconds, TimeUnit.SECONDS)

	# Check if all tasks completed within timeout
	if not finished_in_time:
		executor.shutdownNow()  # Force shutdown remaining tasks
		raise MultiThreadTimeoutError("Not all tasks completed within " + str(timeout_seconds) + " seconds")

	# If there were exceptions during execution, raise them
	if exceptions:
		raise MultiThreadedException(exceptions)

	# Convert results map back to ordered list
	results = []
	for i in range(len(param_list)):
		result = results_map.get(i)
		if isinstance(result, Exception):
			raise result
		elif isinstance(result, dict) and 'exception' in result:
			# Handle error with traceback information
			error_info = result
			original_exception = error_info['exception']
			thread_traceback = error_info['traceback']
			thread_index = error_info['thread_index']

			# Raise a new exception that preserves the original traceback
			raise ThreadExecutionException(original_exception, thread_traceback, thread_index)
		results.append(result)

	return results
