"""
General.Multithreading

This module contains functions for multithreading in Ignition.
"""

import threading
from ast import literal_eval
import General.Utilities

LOGGER = system.util.getLogger("General.Multithreading")

class ExceptionThread(threading.Thread):
	"""
	DESCRIPTION: This wrapper class around the threading.Thread class allows us 
				to catch exceptions in the thread, and re-raise them to the caller
	"""
	def __init__(self, *args, **kwargs):
		"""
		DESCRIPTION: This function initializes the ExceptionThread class
		"""
		super(ExceptionThread, self).__init__(*args, **kwargs)
		self.exception = None
	
	def run(self):
		"""
		DESCRIPTION: This function overrides the run() function of the threading.Thread class, to provide the raised exception
		"""
		self.exception = None
		try:
			super(ExceptionThread, self).run()
		except BaseException as exception: # pylint: disable=broad-except 
			self.exception = exception


class MultiThreadedException(Exception):
	"""
	DESCRIPTION: This exception will take a list of exceptions, and will print them all out when raised.
	PARAMETERS: exceptions (REQ, list[Exception]) - A list of exceptions that were raised
	"""

	def __init__(self, exceptions):
		self.exceptions = exceptions
		if len(self.exceptions) > 1:
			self.message = "Multiple exceptions were raised while multithreading"
		else:
			self.message = "An exception was raised while multithreading"
		
		super(MultiThreadedException, self).__init__(self.message)

	def __str__(self):
		return "%s: %s" % (self.message, self.exceptions)

def wait_for_async_execution(func, kwargs_list=None, max_threads=-1):
	"""
	DESCRIPTION: Executes the function func asynchronously with the parameters in parameter_list
	PARAMETERS: fun (REQ, function) - The function to be executed
				kwargs_list (REQ, list) - A list of dictionaries with the parameters to be passed to the function
				max_threads (OPT, int) - The maximum number of threads to be used.
										 If -1, it will just execute with as many threads as it can
	"""
	if not callable(func):
		if General.Utilities.is_valid_variable_name(func):
			func = literal_eval(func)

	if kwargs_list is None:
		kwargs_list = []
	
	# NOTE: If the number of threads is -1, we will use the number kwargs options provided
	if max_threads == -1:
		max_threads = len(kwargs_list)

	# NOTE: Execute the function in parallel with at most the number of threads in the pool, 
	# and wait for all of them to finish
	threads = []
	for kwargs in kwargs_list:
		thread = ExceptionThread(target=func, kwargs=kwargs)
		thread.start()
		threads.append(thread)

	# NOTE: Wait for all of the threads to finish, and check if any of them raised an exception
	exceptions = []
	for thread in threads:
		thread.join()
		if thread.exception:
			exceptions.append(thread.exception)

	# NOTE: If any of the threads raised an exception, raise a MultiThreadedException
	if exceptions:
		raise MultiThreadedException(exceptions)
