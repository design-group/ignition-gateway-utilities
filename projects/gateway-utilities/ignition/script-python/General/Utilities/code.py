"""
General.Utilities

This module provides functions for general utilities.

This module should not have any dependencies on any other Ignition modules.
"""

LOGGER = system.util.getLogger("General.Utilities")

class JsonPathException(Exception):
	"""
	DESCRIPTION: An exception that occurs when the Json path provided is invalid
	"""

def execute_on_gateway(func):
	"""
	DESCRIPTION: This decorator function wraps an entire function to verify that it is being executed in the correct scope
	"""
	# NOTE: Because this is using gateway scoped files,
	#  we want to make sure that we are aware if this is executed in gateway scope or not
	from com.inductiveautomation.ignition.common.model import ApplicationScope
	scope = ApplicationScope.getGlobalScope()
	is_gateway = ApplicationScope.isGateway(scope)

	def wrapper(*args, **kwargs):
		"""
		DESCRIPTION: This is the wrapper function that will be returned
		"""
		if not is_gateway:
			project = system.util.getProjectName()
			func_path = get_function_qualified_path(func)

			return system.util.sendRequest(project, "executeInGatewayScope", {"func":func_path, 'args':args, 'kwargs':kwargs})

		return func(*args, **kwargs)
	return wrapper


def read_json_path(json_object, json_path):
	"""
	DESCRIPTION: Follows a JSON path to find the needed element. Will also handle a path relating to a list.
					Returns a value based on the path.
	PARAMETERS: path (REQ, str) - a path to the needed value. Can contain . and [].
	"""
	json_path = json_path.split(".")
	current_path = json_path[0]

	value = json_object
	try:
		for item in json_path:
			current_path += ".%s" % item
			if "[" in item:
				# NOTE: Get the number at the end of the path and use it to get the element
				index = int((item[item.find("[")+1]))
				item = item[:item.find("[")]

				# NOTE: Add the most recent index item into the array path
				current_path += "[%s]" % index

				value = value[item][index]
			else:
				value = value[item]

		return value
	except Exception as exception:
			# NOTE: We may be compiling something that we know isnt present sometimes, lets make this null if it isnt
		raise JsonPathException("Failed to read json path for object %s element %s : %s -  EXCEPTION:%s" %
																			(json_path, current_path, value, exception))


def get_function_qualified_path(func):
	"""
	DESCRIPTION: Looks through the file structure of a function and tries to find its fully qualified function path
	PARAMETERS: func (REQ, func) - A function reference

	Example output: General.Files.get_function_qualified_path
	"""
	mqpath = func.func_code.co_filename.split(':', 1)[1].rsplit('>', 1)[0]
	if hasattr(func, 'im_self'):
		mqpath += '.' + func.im_self.__name__
	return '.'.join((mqpath, func.__name__))

def is_valid_variable_name(name):
	"""
	DESCRIPTION: Checks to see if a variable name is valid
	PARAMETERS: name (REQ, str) - The name of the variable
	"""
	from ast import parse

	try:
		parse('%s = None' % (name))
		return True
	except (SyntaxError, ValueError, TypeError):
		return False
