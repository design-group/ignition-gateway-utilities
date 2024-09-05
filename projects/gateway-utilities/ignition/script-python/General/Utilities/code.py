"""
General.Utilities

This module provides functions for general utilities.

This module should not have any dependencies on any other Ignition modules.
"""
import collections
import java.lang.Exception
import json
import os
import re
from com.inductiveautomation.ignition.common.model import ApplicationScope

LOGGER = system.util.getLogger("General.Utilities")
GLOBAL_SCOPE = ApplicationScope.getGlobalScope()

class JsonPathException(Exception):
	"""
	DESCRIPTION: An exception that occurs when the Json path provided is invalid
	"""

def get_system_name():
	"""
	DESCRIPTION: Returns the name of the system
	PARAMETERS: None
	RETURNS: str - The name of the system
	"""
	return system.tag.readBlocking("[System]Gateway/SystemName")[0].value

def receive_execute_on_gateway_message(payload):
	"""
	DESCRIPTION: This message handler will be called each time a message of this type is received.
	PARAMETERS: payload (REQ, dict) - A dictionary that holds the objects passed to this message handler

	Example call in project scope: 
		system.util.sendRequest(project, "executeInGatewayScope", 
			{"func":"myScript.myFunction", 'kwargs':{"myParam1":123,"myParam2":456}}), 
	RETURNS: obj - The result of the function call
	"""
	if payload.get('func') is None:
		raise TypeError("executeInGatewayScope expects a payload object named func")
	
	func_reference = eval(payload['func']) # pylint: disable=eval-used
	args = payload.get('args', [])
	kwargs = payload.get('kwargs', {})
	
	if payload.get('root_server'):
		kwargs['root_server'] = payload.get('root_server')

	return func_reference(*args, **kwargs)

def execute_on_gateway(timeout_seconds=60, remote_server=None, func_path=None):
	"""
	DESCRIPTION: This decorator function wraps an entire function to verify that it is being executed in the correct scope
	PARAMETERS: timeout_seconds (OPT, int) - The amount of time to wait for the function to execute
				remote_server (OPT, str) - The remote server to execute on
				func_path (OPT, str) - The path to the function to execute
	RETURNS: obj - The result of the function call
	"""
	if remote_server == get_system_name():
		remote_server = None
	
	
	def wrapper(func):
		"""
		DESCRIPTION: Initialize wrapper function
		"""
		def gateway_function_wrapper(*args, **kwargs):
			"""
			DESCRIPTION: This is the wrapper function that will be returned
			"""
			# NOTE: If this is a nested wrapper, we need to get the function path from the previous wrapper; set a local var
			wrap_func_path = func_path 

			# If root server was passed in, we should remove it because this function wont re-send
			if 'root_server' in kwargs:
				del kwargs['root_server']
				return func(*args, **kwargs)
			
			# NOTE: If the call is not in the gateway scope, OR we are calling a remote server, then we should execute.
			if not is_gateway_scope() or remote_server:
				project = system.util.getProjectName()
				# NOTE: If we dont have a function path, then we need to get it from the function to pass to the gateway
				if wrap_func_path is None:
					wrap_func_path = get_function_qualified_path(func)
				return system.util.sendRequest(project, "executeInGatewayScope", 
													{"func":wrap_func_path, 'args':args, 'kwargs':kwargs}
													, timeoutSec=timeout_seconds, remoteServer=remote_server)
			#function_wrapper
			return func(*args, **kwargs)
		#wrapper
		return gateway_function_wrapper
	#execute_on_gateway
	return wrapper

def execute_on_gateways(remote_servers=None, func_path=None):
	"""
	DESCRIPTION: This decorator function wraps an entire function to verify that it is being executed in the correct scope
	PARAMETERS: remote_servers (OPT, list) - A list of remote servers to execute on
				func_path (OPT, str) - The path to the function to execute
	RETURNS: obj - The result of the function call
	"""
	system_name = get_system_name()
	
	def wrapper(func):
		"""
		Description: Initialize wrapper function
		"""
		def function_wrapper(*args, **kwargs):
			"""
			DESCRIPTION: This is the wrapper function that will be returned
			"""

			LOGGER.debug("Debug: executing %s on %s, remote_servers: %s, root server: %s" 
							% (func_path, system_name, remote_servers, kwargs.get('root_server')))
			
			# NOTE: If this is a nested wrapper, we need to get the function path from the previous wrapper; set a local var
			wrap_func_path = func_path 

			if wrap_func_path is None:
				wrap_func_path = get_function_qualified_path(func)
			project = system.util.getProjectName()
		
			# NOTE: If this was tagged with a root server, we should execute it here, as we were called to
			if kwargs.get('root_server'):
				kwargs.pop('root_server')
				return func(*args, **kwargs)


			for remote_server in remote_servers:
				try:
					if remote_server == system_name:
						remote_server = None
					return system.util.sendRequest(project, "executeInGatewayScope", 
								{"func":wrap_func_path, 'args':args, 'kwargs':kwargs, 'root_server':system_name}
							, timeoutSec=10, remoteServer=remote_server)
				except (java.lang.Exception, Exception) as e:
					LOGGER.error("Failed to execute on remote gateway %s: %s" 
				  					% (remote_server, {"func":wrap_func_path, 'args':args, 'kwargs':kwargs, 'root_server':system_name}))
					raise e

		#wrapper: 
		return function_wrapper
	#execute_on_gateway
	return wrapper

def read_json_path(json_object, json_path):
	"""
	DESCRIPTION: Follows a JSON path to find the needed element. Will also handle a path relating to a list.
					Returns a value based on the path.
	PARAMETERS: path (REQ, str) - a path to the needed value. Can contain . and [].
	RETURNS: obj - The value of the path
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
def is_valid_json(data):
	"""
	DESCRIPTION: Checks to see if a string is valid JSON
	PARAMETERS: data (REQ, str) - The string to be checked
	RETURNS: bool - True if the string is valid JSON, False if it is not
	"""
	try:
		if isinstance(data, dict):
			json.dumps(data)
		else:
			json.loads(data)
		return True
	except ValueError:
		return False
	except TypeError:
		return False

def get_function_qualified_path(func):
	"""
	DESCRIPTION: Looks through the file structure of a function and tries to find its fully qualified function path
	PARAMETERS: func (REQ, func) - A function reference

	Example output: General.Files.get_function_qualified_path
	RETURNS: str - The fully qualified path of the function
	"""
	mqpath = func.func_code.co_filename.split(':', 1)[1].rsplit('>', 1)[0]
	if hasattr(func, 'im_self'):
		mqpath += '.' + func.im_self.__name__
	return '.'.join((mqpath, func.__name__))

def is_valid_variable_name(name):
	"""
	DESCRIPTION: Checks to see if a variable name is valid
	PARAMETERS: name (REQ, str) - The name of the variable
	RETURNS: bool - True if the variable name is valid, False if it is not
	"""
	from ast import parse

	try:
		parse('%s = None' % (name))
		return True
	except (SyntaxError, ValueError, TypeError):
		return False
	
def sort_list_by_alpha_numeric(the_list, key='label'):
	"""
	DESCRIPTION: Sorts a list alphabetically
	PARAMETERS: the_list (REQ, list): the list to be converted
	RETURNS: list - The sorted list
	"""
	LOGGER.trace("sort_list_by_alpha_numeric(the_list=%s)" % (the_list))
	try:
		return sorted(the_list, key=lambda val: (re.sub(r'\d+', "", val), int(re.sub(r'\D+', "", val) or 0)))
	except TypeError:
		return sorted(the_list, key=lambda val: (re.sub(r'\d+', "", val.get(key)), 
						int(re.sub(r'\D+', "", val.get(key)) or 0)))

def round_to_next_hour(datetime):
	"""
	DESCRIPTION: Rounds value up to the nearest hour
	PARAMETERS: datetime (REQ, datetime): The value to be rounded up
	RETURNS: java.util.Date: The rounded up value
	"""
	year = system.date.getYear(datetime)
	day_of_year = system.date.getDayOfYear(datetime)
	hour_plus_one = system.date.getHour24(datetime) + 1
	
	# this ticks the date over if the hour is rounded to midnight
	if hour_plus_one == 0 or hour_plus_one == 24:
		day_of_year += 1
	
	return system.date.parse("%s-%s %s:00:00" % (year, day_of_year, hour_plus_one), "y-D k:m:s")

def get_from_path(obj, path):
	"""
	DESCRIPTION: Splits path and adds each part of path to a return value associated with the object
	PARAMETERS: object (REQ, object): The object the path will be associated to
				path (REQ, string): The path to be seperated and then associated to the object
	RETURNS: obj - The value of the path
	"""
	keys = path.split('.')
	rv = obj
	for key in keys:
		rv = rv[key]
	return rv

def combine_objects(base_dict, dict_to_merge, prepend_list=False):
	""" 
	DESCRIPTION: This method takes 2 objects and returns a combined object without overwriting any of the keys or values
	PARAMETERS: dct (REQ, dictionary) -  dict onto which the merge is executed
				merge_dct (REQ, dictionary) - dct merged into dct
				prepend_list (OPT, boolean) - if true, the merge_dct is prepended to the base_dict
	RETURNS: dict - The combined object
	"""
	for k in dict_to_merge.keys():
		if (k in base_dict and isinstance(base_dict[k], dict)
				and isinstance(dict_to_merge[k], collections.Mapping)):
			combine_objects(base_dict[k], dict_to_merge[k])
		elif k in base_dict and isinstance(base_dict[k], list) and isinstance(dict_to_merge[k], list):
			if prepend_list:
				base_dict[k] = list(dict_to_merge[k]) + base_dict[k]
			else:
				base_dict[k].extend(dict_to_merge[k])
		else:
			base_dict[k] = dict_to_merge[k]
	return base_dict

def get_millis_time():
	"""
	DESCRIPTION: Returns the current time in milliseconds
	PARAMETERS: None
	RETURNS: int: The current time in milliseconds
	"""
	return system.date.toMillis(system.date.now())

def is_number(val):
	"""
	DESCRIPTION: Takes a string value and attempts to convert it to a float, if successful it wont error. 
				 If it errors, it likely isnt a valid number.
	PARAMETERS: val (REQ, obj) - A value which to compare to a float
	"""
	try:
		float(val)
		return True
	except (ValueError, TypeError):
		return False
	
def is_designer_scope():
	"""
	DESCRIPTION: Checks to see if the current scope is the designer
	PARAMETERS: None
	RETURNS: bool - True if the current scope is the designer, False if it is not
	"""
	return ApplicationScope.isDesigner(GLOBAL_SCOPE)

def is_gateway_scope():
	"""
	DESCRIPTION: Checks to see if the current scope is the gateway
	PARAMETERS: None
	RETURNS: bool - True if the current scope is the gateway, False if it is not
	"""
	return ApplicationScope.isGateway(GLOBAL_SCOPE)

def is_perspective_scope():
	"""
	DESCRIPTION: Checks to see if the current scope is perspective
	PARAMETERS: None
	RETURNS: bool - True if the current scope is perspective, False if it is not
	"""
	return ApplicationScope.isGateway(GLOBAL_SCOPE) and hasattr(system, 'perspective')

def is_vision_scope():
	"""
	DESCRIPTION: Checks to see if the current scope is vision
	PARAMETERS: None
	RETURNS: bool - True if the current scope is vision, False if it is not
	"""
	return ApplicationScope.isClient(GLOBAL_SCOPE)

def get_environment_variable(name):
	"""
	DESCRIPTION: Gets an environment variable from the system
	PARAMETERS: name (REQ, str) - The name of the environment variable
	RETURNS: str - The value of the environment variable
	"""
	return os.environ.get(name)
	
def localize_object(obj, locale):
	"""
	DESCRIPTION: Converts properties from the view into a dictionary, if possible and translates
	PARAMETERS: obj (REQ, object): The properties to be converted
				locale (REQ, string): The locale to which the object has to be translated
	RETURNS: dict (dict): The dictionary of the properties with translated values
	"""
	if obj is None:
		return None

	# NOTE: If this is a basic qualified value, and not a dictionary with the key 'value', 
	# then replace the object with its value
	if hasattr(obj, 'value') and not hasattr(obj, 'keys'):
		obj = obj.value

	# NOTE: Then check for any kind of dictionary or list
	if hasattr(obj, '__iter__'):
		if hasattr(obj, 'keys'):
			return dict((k, localize_object(obj[k], locale)) for k in obj.keys())
		else:
			return list(localize_object(x, locale) for x in obj)
	else:
		# anything else
		if isinstance(obj, (str, unicode)):
			obj = system.util.translate(obj, locale)
		
		return obj
