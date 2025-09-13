"""
General.Conversion

This module contains functions for converting data types.

This module should not have any dependencies on any other Ignition modules.
"""
import re
import collections
from java.util import Date as JavaDate

LOGGER = system.util.getLogger("General.Conversion")


def convert_dataset_to_list(dataset, date_to_millis=False):
	"""
	DESCRIPTION: This function converts a dataset to a list of dictionaries 
	PARAMETERS: dataset (REQ, dataset): The dataset to be converted to a list of dictionaries
				date_to_millis (OPT, bool): True if the date should be converted to milliseconds
	"""
	LOGGER.trace("convert_dataset_to_list(dataset=%s)" % (dataset))

	if not hasattr(dataset, "getColumnNames"):
		return dataset

	column_names = dataset.getColumnNames()

	data = []

	for row in range(dataset.getRowCount()):
		row_data = {}
		for column in range(dataset.getColumnCount()):
			value = dataset.getValueAt(row, column)
			if date_to_millis and value and isinstance(value, JavaDate):
				value = system.date.toMillis(value)

			row_data[column_names[column]] = value
		data.append(row_data)
	return data


def convert_list_to_dataset(list_var, titalize_headers=False, column_order=None, headers_list=None):
	"""
	DESCRIPTION: This function converts list of dictionaries to a dataset
	PARAMETERS: list_var (REQ, list): The list of dictionaries to be converted
				titalize_headers (OPT, bool): True in the case of the ability to get the names of the header in list_var
				column_order (OPT, list): List of columns to include and their order in the resulting dataset
				headers_list (OPT, list): List of headers to use instead of keys from list_var
	RETURN: Compiled dataset from the list of dictionaries
	"""

	def type_conversion(value, target_type, allow_mixed=False):
		"""
		DESCRIPTION: This function converts list of dictionaries to a dataset
		PARAMETERS: list_var (REQ, list): The list of dictionaries to be converted
					titalize_headers (OPT, bool): True in the case of the ability to get the names of the header in list_var
					column_order (OPT, list): List of columns to include and their order in the resulting dataset
					headers_list (OPT, list): List of headers to use instead of keys from list_var
		"""
		if value is None:
			return None
		#NOTE: If the value is already the target type, return it
		if isinstance(value, target_type):
			return value
		#NOTE: Attempt to convert the value to the target type
		try:
			return target_type(value)
		except (ValueError, TypeError):
			#NOTE: Return original value if mixed types are allowed, otherwise None
			return value if allow_mixed else None

	if not isinstance(list_var, collections.Iterable) or not list_var:
		return list_var

	if headers_list is not None:
		headers = column_names = headers_list
	elif column_order is not None:
		headers = column_names = column_order
	else:
		headers = column_names = sorted(list_var[0].keys())

	if titalize_headers:
		headers = [name.title() for name in column_names]

	#NOTE: Determine types for each column
	key_type_map = {}
	key_mixed_types = {}
	for key in column_names:
		types = {type(row.get(key)) for row in list_var if row.get(key) is not None}
		if float in types:
			types = {float}

		#NOTE: Check if we have mixed types (excluding None)
		key_mixed_types[key] = len(types) > 1

		#NOTE: If we have mixed types, default to string
		if key_mixed_types[key]:
			key_type_map[key] = str
		else:
			key_type_map[key] = list(types)[0] if types else str

	data = []
	for row in list_var:
		row_data = []
		for column in column_names:
			value = row.get(column)
			#NOTE: Handle styled values
			if hasattr(value, "get"):
				value = value.get("value")

			#NOTE: Use allow_mixed=True for columns with mixed types
			row_data.append(type_conversion(value, key_type_map[column], allow_mixed=key_mixed_types[column]))

		data.append(row_data)

	return system.dataset.toDataSet(headers, data)


def convert_properties_to_dictionary(obj):
	"""
	DESCRIPTION: Converts properties from the view into a dictionary, if possible
	PARAMETERS: obj (REQ, object): The properties to be converted
	"""
	LOGGER.trace("convert_properties_to_dictionary(obj=%s)" % (obj))

	if obj is None:
		return None

	#NOTE: If this is a basic qualified value, and not a dictionary with the key "value",
	#NOTE: then replace the object with its value
	if hasattr(obj, "value") and not hasattr(obj, "keys"):
		obj = obj.value

	#NOTE: Then check for any kind of dictionary or list
	if hasattr(obj, "__iter__"):
		if hasattr(obj, "keys"):
			return dict((k, convert_properties_to_dictionary(obj[k])) for k in obj.keys())
		else:
			return list(convert_properties_to_dictionary(x) for x in obj)
	else:
		#NOTE: anything else
		return obj

def convert_from_camel_case_to_caps(string):
	"""
	DESCRIPTION: Converts a string from camel case to all caps
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to all caps
	"""
	LOGGER.trace("convert_from_camel_case_to_caps(string=%s)" % (string))
	return re.sub("([a-z])([A-Z])", r"\g<1> \g<2>", string).capitalize()

def convert_snake_case_to_camel_case(string):
	"""
	DESCRIPTION: Converts a string from snake case (standard within scripts) to camel case (standard within Ignition props)
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to camel case
	"""
	string = "".join(char.capitalize() for char in string.lower().split("_"))
	return string[0].lower() + string[1:]

def convert_list_to_dropdown(options):
	"""
	DESCRIPTION: Creates a list of dictionaries for each object to allow for a dropdown option
	PARAMETERS: options (REQ, list): The list of values possible for a drop down
	RETURNS: list (list): The list of dictionaries for the dropdown
	"""
	LOGGER.trace("convert_list_to_dropdown(options=%s)" % (options))
	dropdown_options = []
	for option in options:
		if isinstance(option, basestring):
			dropdown_options.append({"label": option, "value": option})
		elif isinstance(option, collections.Mapping):
			dropdown_options.append(option)
	return dropdown_options

def convert_dict_to_dropdown(options):
	"""
	DESCRIPTION: Creates a list of dictionaries for a dropdown from a dictionary
	PARAMETERS: options (REQ, dict): The dictionary to be converted (key is the label, value is the value)
	RETURNS: list (list): The list of dictionaries for the dropdown
	"""
	LOGGER.trace("convert_dict_to_dropdown(options=%s)" % (options))
	dropdown_options = []
	for key in options.keys():
		dropdown_options = [{"label": val, "value": key} for key, val in options.iteritems()]
	return sorted(dropdown_options, key=lambda opt: opt["value"])

def convert_seconds_to_str_format(seconds):
	"""
	DESCRIPTION: Converts seconds to a string in the format of HH:MM:SS
	PARAMETERS: seconds(str) - The number of seconds to convert
	RETURNS: A string in the format of HH:MM:SS
	"""
	LOGGER.trace("convert_str_to_seconds(seconds=%s)" % (seconds))
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return "%d:%02d:%02d" % (hour, minutes, seconds)
