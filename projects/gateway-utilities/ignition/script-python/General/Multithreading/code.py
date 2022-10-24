import threading
logger = system.util.getLogger("General.Multithreading")

try:
	if not hasattr(General, "Utilities"):
		raise NameError("General.Utilities not found")
except NameError as e:
	logger.warn("Some Features of this script module require other modules, please ensure that each required module is properly loaded or some functionality might not work: %s" % e.message)


class ExceptionThread(threading.Thread):
	"""
	DESCRIPTION: This wrapper class around the threading.Thread class allows us to catch exceptions in the thread, and re-raise them to the caller
	"""
	def run(self):
		"""
		DESCRIPTION: This function overrides the run() function of the threading.Thread class, to provide the raised exception
		"""
		self.exception = None           
		try:
			super(ExceptionThread, self).run()
		except BaseException as e:
			self.exception = e


class MultiThreadedException(Exception):
	"""
	DESCRIPTION: This exception will take a list of exceptions, and will print them all out when raised.
	PARAMETERS: exceptions (REQ, list[Exception]) - A list of exceptions that were raised
	"""

	def __init__(self, exceptions):
		self.exceptions = exceptions
		super(MultiThreadedException, self).__init__("Multiple exceptions were raised")
	
	def __str__(self):
		return "Multiple exceptions were raised: %s" % self.exceptions

def wait_for_async_execution(func, kwargs_list=[], max_threads=-1):
	"""
	DESCRIPTION: Executes the function func asynchronously with the parameters in parameter_list
	PARAMETERS: fun (REQ, function) - The function to be executed
				kwargs_list (REQ, list) - A list of dictionaries with the parameters to be passed to the function
				max_threads (OPT, int) - The maximum number of threads to be used. If -1, it will just execute with as many threads as it can
	"""
	if not callable(func):
		if General.Utilities.is_valid_variable_name(func):
			func = eval(func)
	
	# NOTE: If the number of threads is -1, we will use the number kwargs options ptovided
	if max_threads == -1:
		max_threads = len(kwargs_list)

	# NOTE: Execute the function asynchronously with at most the number of threads in the pool, and wait for all of them to finish
	threads = []
	for kwargs in kwargs_list:
		t = ExceptionThread(target=func, kwargs=kwargs)
		t.start()
		threads.append(t)
	
	# NOTE: Wait for all of the threads to finish, and check if any of them raised an exception
	exceptions = []
	for t in threads:
		t.join()
		if t.exception:
			exceptions.append(t.exception)
	
	# NOTE: If any of the threads raised an exception, raise a MultiThreadedException
	if len(exceptions) > 0:
		raise MultiThreadedException(exceptions)