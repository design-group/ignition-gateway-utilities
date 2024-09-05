"""
General.Errors
This module contains functions for handling errors in Ignition.
"""
import sys
import linecache
from java.lang import Throwable

LOGGER = system.util.getLogger("General.Errors")

class ExceptionWithDetails(Exception):
	"""
	DESCRIPTION: This class is a custom exception that will log the exception message and stack trace.
	PARAMETERS:
		exception_message (str): The message to be logged.
	"""
	def __init__(self, exception_message=None, logger=LOGGER, exception=None):
		if isinstance(exception, ExceptionWithDetails):
			self.__dict__.update(exception.__dict__)
			return 
		
		stack_trace = Throwable(str(exception_message))
		message_contents = []
		if isinstance(self, ExceptionWithDetails):
			exception_details = get_exception()
			message_contents.append("EXCEPTION: %s" % exception_details)
		
			if exception_message is not None:
				message_contents.append("MESSAGE: %s" % exception_message)
			
			if hasattr(exception, 'getCause'):
				cause = exception.getCause()
				if hasattr(cause, 'getMessage'):
					message_contents.append("CAUSE: %s" % cause.getMessage())

				if hasattr(cause, 'getStackTrace'):
					stack_trace.setStackTrace(cause.getStackTrace())

		else:
			message_contents.append(exception_message)
		
		self.message = ', '.join(message_contents)
		
		# NOTE: IF this is a direct exception with details, lets throw it in the logs
		if isinstance(self, ExceptionWithDetails):
			logger.error(self.message, stack_trace)

		super(ExceptionWithDetails, self).__init__(self.message)

def get_exception():
	"""
	If you put this in a generic try...except block that continues to raise the error, you can cleanly get a 
	defined error message in the logs, without changing applciation logic.
	
	Example Error: 
		(<module:General.Conversion>, LINE 270 ""): sequence item 0: expected string, NoneType found
	
	Example Use:
		try:
			# Execute code here	
		except Exception as e:
			LOGGER.error(General.Errors.get_exception())
			raise(e)
	"""
	exc_type, exc_obj, tb = sys.exc_info()

	f = tb.tb_frame
	lineno = tb.tb_lineno
	filename = f.f_code.co_filename
	linecache.checkcache(filename)
	line = linecache.getline(filename, lineno, f.f_globals)
	return '{}({}, LINE {} "{}"): {}'.format(exc_type.__name__, filename, lineno, line.strip(), exc_obj)
