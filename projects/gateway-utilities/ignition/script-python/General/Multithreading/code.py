"""
General.Multithreading

This module contains functions for multithreading in Ignition.
"""

from ast import literal_eval
import General.Utilities
from java.lang import Thread
from java.lang import Runnable
from java.util.concurrent import Executors
from java.util.concurrent import ThreadFactory
from java.util.concurrent import TimeUnit
from com.inductiveautomation.ignition.common.script import ScriptContext

from com.inductiveautomation.ignition.common.execution import TPC

LOGGER = system.util.getLogger("General.Multithreading")
MULTITHREADING_SYSTEM_NAME = "Multithreading"

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

class AsyncThreadFactory(ThreadFactory):
	"""
	DESCRIPTION: A java.util.concurrent.ThreadFactory that will create threads with a name.
	"""
	def __init__(self, name, exception_handler):
		self.name = name
		self.exception_handler = exception_handler
		self.thread_factory = TPC.newThreadFactory(self.name, MULTITHREADING_SYSTEM_NAME)
	
	# This is a java function, so we have to ignore the invalid name
	def newThread(self, runnable): # pylint: disable=invalid-name
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

def wait_for_async_execution(func, kwargs_list=None, max_threads=-1, timeout_seconds=10):
	"""
	DESCRIPTION: Executes the function func asynchronously with the parameters in parameter_list
	PARAMETERS: func (REQ, function) - The function to be executed
				kwargs_list (REQ, list) - A list of dictionaries with the parameters to be passed to the function
				max_threads (OPT, int) - The maximum number of threads to be used.
										 If -1, it will just execute with as many threads as it can
				timeout_seconds (OPT, int) - The maximum number of seconds to wait for the threads to finish
	"""
	# NOTE: If our function showed up as a name, we would have to use the following line to get the actual function
	if not callable(func):
		if General.Utilities.is_valid_variable_name(func):
			func = literal_eval(func)

	# NOTE: If there are no kwargs, we will just make an empty list, but the function will be executed once
	if kwargs_list is None:
		kwargs_list = [None]

	# NOTE: If the number of threads is -1, we will use the number kwargs options provided
	if max_threads == -1:
		max_threads = len(kwargs_list)
	
	# Define an exception handler that will be used to bubble up exceptions
	exceptions = []
	class AsyncExceptionHandler(Thread.UncaughtExceptionHandler):
		# This is a java function, so we have to ignore the invalid name
		def uncaughtException(self, thread, exception): # pylint: disable=invalid-name
			exceptions.append((thread, exception))
	
	function_name = General.Utilities.get_function_qualified_path(func)
	# NOTE: Execute the function in parallel with at most the number of threads in the pool, 
	# and wait for all of them to finish
	executor = Executors.newFixedThreadPool(max_threads, AsyncThreadFactory(function_name, AsyncExceptionHandler()))

	for i in range(len(kwargs_list)):
		executor.execute(FunctionWrapper(func, kwargs=kwargs_list[i]))
		
	executor.shutdown()
	executor.awaitTermination(timeout_seconds, TimeUnit.SECONDS)

	if exceptions:
		raise MultiThreadedException(exceptions)
