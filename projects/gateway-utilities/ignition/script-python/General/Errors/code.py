"""
General.Errors
This module contains functions for handling errors in Ignition.
"""
from __future__ import print_function
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
	# pylint: disable=invalid-name
	def __init__(self, exception_message=None, logger=LOGGER, exception=None, user_message=None):
		if isinstance(exception, ExceptionWithDetails):
			self.__dict__.update(exception.__dict__)
			return 

		if user_message is not None:
			self.user_message = user_message

		stack_trace = Throwable(str(exception_message))
		message_contents = []
		if type(self) == ExceptionWithDetails: # pylint: disable=unidiomatic-typecheck
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
		if type(self) == ExceptionWithDetails: # pylint: disable=unidiomatic-typecheck
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

def print_error(source_logger, error_message=None, session_id=None, page_id=None):
	"""
	DESCRIPTION: Prints an error to the console and the logs.
	PARAMETERS: source_logger (logger, REQ): The LOGGER to use for logging the error.
				error_message (string, OPT): The error message to print.
				sessionId (string, OPT): The session ID to print the error to.
				pageId (string, OPT): The page ID to print the error to.
	"""
	LOGGER.trace("General.Errors.print_error(source_logger=%s, error_message=%s, session_id=%s, page_id=%s)" \
	 										% (source_logger, error_message, session_id, page_id))
	source_logger.error(error_message)
	print(error_message)
	
	if session_id and page_id:
		system.perspective.print(error_message, session_id, page_id)

