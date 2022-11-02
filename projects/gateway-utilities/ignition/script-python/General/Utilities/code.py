"""
General.Utilities

This module provides functions for general utilities.

This module should not have any dependencies on any other Ignition modules.
"""
import re
import collections
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

			return system.util.sendRequest(project, "executeInGatewayScope", 
												{"func":func_path, 'args':args, 'kwargs':kwargs})

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
	
def sort_list_by_alpha_numeric(the_list, key='label'):
	"""
	DESCRIPTION: Sorts a list alphabetically
	PARAMETERS: the_list (REQ, list): the list to be converted
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
