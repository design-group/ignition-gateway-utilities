# NOTE: We must import the printing function from python 3 so that it doesn't compile the system.perspective.print as a failure
from __future__ import print_function

import sys, os, json

try:
	system.util
	from java.lang import Throwable
	_logger_disabled = False
except (NameError, AttributeError, ImportError):
	""" This is in Ignition, we dont need to import code with file paths added """
	sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, 'ignition/script-python')))
	_logger_disabled = True
# NOTE: basestring was changed to be str in python 3.0
if sys.version_info >= (3, 0):
    basestring = str
	

class LoggingException(Exception):
	pass

class Logger(object):
	
	def __init__(self, logger_name, parent_logger=None):
		"""
		DESCRIPTION: instantiates object
		PARAMETERS: logger_name (REQ, string) - name of the logger
        """
		# NOTE: If we are provided a class instance instead of a logger name, just take the class name
		if not isinstance(logger_name, basestring):
			logger_name = logger_name.__class__.__name__

		self._logger_name = logger_name

		if not _logger_disabled:

			self.parent_logger = parent_logger

			if parent_logger:
				self.logger = parent_logger.logger.createSubLogger(self._logger_name)
			else:
				self.logger = system.util.getLogger(self._logger_name)

		
	def get_logging_method(self, level):
		logging_levels = {
			"info": (self.logger.info, self.logger.isInfoEnabled),
			"trace": (self.logger.trace, lambda: True),
			"debug": (self.logger.debug, self.logger.isDebugEnabled),
			"warn": (self.logger.warn, lambda: True),
			"error": (self.logger.error, lambda: True)
			}
		
		return logging_levels.get(level, "info")


	def get_name(self):
		"""
		DESCRIPTION: gets the name of the logger
		if else used to check if run in python or Ignition.
		"""
		if not _logger_disabled:
			return self.logger.getName()
		else:
			return self._logger_name

	def create_sub_logger(self, logger_name):
		"""
		DESCRIPTION: creates sub logger of a parent logger
		PARAMETERS: logger_name (REQ, string) - the name for the sub logger
		"""
		if not isinstance(logger_name, basestring):
			logger_name = logger_name.__class__.__name__
		if not _logger_disabled:
			new_logger = type(self)(logger_name, parent_logger=self)
			return new_logger
		else:
			new_logger = type(self)("%s.%s" % (self.get_name(), logger_name))
			return new_logger

	def build_throwable(self, detail_object):
		""" 
		DESCRIPTION: Builds a throwable object from a python object, decoding it to json if possible
		PARAMETERS: detail_object (REQ, object) - the object to be converted to a throwable for printing in the logs
		"""
		try:
			object_string = json.dumps(detail_object)
		except TypeError:
			object_string = str(detail_object)

		detailed_throwable = Throwable(object_string)

		# NOTE: This removes the stack trace from the throwable
		detailed_throwable.setStackTrace([])

		return detailed_throwable
	


	def detailed_log(self, log_method, message, details=None):
		"""
		DESCRIPTION: Determines if a detailed log can occur if not, just log regularly
		PARAMETERS: log_method (REQ, method) The logging method which will be executed
					details (OPT, object) - the object to be converted to a throwable for printing in the logs
        """
		if details is not None:
			log_method(message, self.build_throwable(details))
		else:
			log_method(message)
	
		
	def generic_log(self, logger_message, logger_details, logging_level):
		"""
		DESCRIPTION: calls the method which makes the log, repeats using parent log if necessary.
		PARAMETERS: logger_message(REQ, string) The message to be logged
					logger_details (REQ, object) - the object to be converted to a throwable for printing in the logs
					logging_level (REQ, string) - the Ignition specific level the gateway will be logged to
		"""
		custom_message = "%s.%s: %s" % (self.get_name(), logging_level, logger_message)

		if _logger_disabled:
			self.custom_print(custom_message)
		else:
			try:
				# NOTE: get needed method and information based on the logging level then log it using the detailed_log method
				logging_method, logger_enabled = self.get_logging_method(logging_level)
				self.detailed_log(logging_method, logger_message, logger_details)
			
			except:
				# NOTE: if we weren't able to use the main logger, repeat above but with the parent logger
				if self.parent_logger:
					self.parent_logger.generic_log(logger_message, logger_details, logging_level)

			if logger_enabled():
				self.custom_print(custom_message)
	
	def info(self, logger_message, logger_details=None):
		"""
		DESCRIPTION: Logs to the gateway with the logging level set to INFO, valuable for general details that we would want to show up in any logs for historical troubleshooting.
		PARAMETERS: logger_message (REQ, string) - the message to be recorded in log
					logger_details (OPT, object) - the object to be converted to a throwable for printing in the logs
        """
		self.generic_log(logger_message, logger_details, "info")

	def error(self, logger_message, logger_details=None):
		"""
		DESCRIPTION: Logs to the gateway with the logging level set to ERROR, valuable for calling out errors that happened in the application, for historical and real time troubleshooting.
		PARAMETERS: logger_message (REQ, string) - the message to be recorded in log
					logger_details (OPT, object) - the object to be converted to a throwable for printing in the logs
        """
		self.generic_log(logger_message, logger_details, "error")

	def trace(self, logger_message, logger_details=None):
		"""
		DESCRIPTION: Logs to the gateway with the logging level set to TRACE, valuable for finer level details that normally are not logged.
		PARAMETERS: logger_message (REQ, string) - the message to be recorded in log
					logger_details (OPT, object) - the object to be converted to a throwable for printing in the logs
		"""
		self.generic_log(logger_message, logger_details, "trace")

	def debug(self, logger_message, logger_details=None):
		"""
		DESCRIPTION: Logs to the gateway with the logging level set to DEBUG, valuable for adding troubleshooting information into the logs, that shouldn't always be present.
		PARAMETERS: logger_message (REQ, string) - the message to be recorded in log
					logger_details (OPT, object) - the object to be converted to a throwable for printing in the logs
        """
		self.generic_log(logger_message, logger_details, "debug")
		


	def warn(self, logger_message, logger_details=None):
		"""
		DESCRIPTION: Logs to the gateway with the logging level set to WARN, valuable for displaying warnings to a user in the logs that should likely be resolved.
		PARAMETERS: logger_message (REQ, string) - the message to be recorded in log
					logger_details (OPT, object) - the object to be converted to a throwable for printing in the logs
        """
		custom_message = "%s.warn: %s" % (self._logger_name, logger_message)
		if _logger_disabled:
			self.custom_print(custom_message)
		else:
			if logger_details is not None:
				self.logger.warn(logger_message, self.build_throwable(logger_details))
			else:
				self.logger.warn(logger_message)
			
			# isWarnEnabled does not exist, so we will just print
			self.custom_print(custom_message)


	def custom_print(self, custom_message):
		"""
		DESCRIPTION: Allows for printing to console in the python, client, and perspective scopes. Catch all for above functions.
		PARAMETERS: custom_message (REQ, string) - the message to be recorded in the console
        """
		
		if _logger_disabled:
			sys.stdout.write("%s\n" % custom_message)
		else:
			try:
				system.perspective.print(custom_message)
			except:
				sys.stdout.write("%s\n" % custom_message)



class FileLogger():
	def __init__(self, delimiter="`"):
		"""
		DESCRIPTION: instantiates object, creates instance of the Logger class to allow logging directly to a log file, but not the gateway logs.
		PARAMETERS: delimiter (OPT, string) - What separates the values in the log
        """
		self.delimiter = delimiter
		if not _logger_disabled:
			self.file_logger = system.util.getLogger("tms-transaction-log")
		else:
			self.file_logger = Logger("tms-transaction-log")
			
		self.gateway_logger = Logger("Logging.FileLogger")

	def format_log(self, logger_message):
		"""
		DESCRIPTION: creates a string with a delimiter to parse each value
		PARAMETERS: logger_message (REQ, list) - the message to be recorded in log
        """
		if not isinstance(logger_message, list):
			raise LoggingException("logger_message must be a list, provided: %s" % (type(logger_message)))

		return self.delimiter.join(logger_message)

	def log_to_file(self, logger_message):
		"""
		DESCRIPTION: writes the logger message to a csv file
		PARAMETERS: logger_message (REQ, list) - the message to be recorded in log
		"""
		self.gateway_logger.trace("Logging to file: %s" % logger_message)
		formatted_message = self.format_log(logger_message)
		self.file_logger.info(formatted_message)
