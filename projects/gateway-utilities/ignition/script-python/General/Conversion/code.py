"""
General.Conversion

This module contains functions for converting between various string cases and data types.
It is designed to be independent of other Ignition modules to ensure maximum reusability.
This module should not have any dependencies on any other Ignition modules.

Supported case types:
- Camel Case:  camelCase
- Pascal Case: PascalCase
- Snake Case:  snake_case
- Kebab Case:  kebab-case
- Title Case:  Title Case
- Sentence Case: Sentence case
- Upper Case: UPPER CASE
"""
import re
import collections

LOGGER = system.util.getLogger("General.Conversion")

def convert_dataset_to_list(dataset):
	"""
	DESCRIPTION: This function converts a dataset to a list of dictionaries 
	PARAMETERS: dataset (REQ, dataset): The dataset to be converted to a list of dictionaries
	RETURNS: list (list): The list of dictionaries
	"""
	LOGGER.trace("convert_dataset_to_list(dataset=%s)" % (dataset))
	if dataset is None:
		return dataset
	if isinstance(dataset, collections.Iterable):
		return dataset
	if isinstance(dataset, (int, long)):
		return dataset
	if isinstance(dataset, str):
		return dataset

	column_names = dataset.getColumnNames()

	data = []
	
	for row in range(dataset.getRowCount()):
		row_data = {}
		for column in range(dataset.getColumnCount()):
			row_data[column_names[column]] = dataset.getValueAt(row, column)
		data.append(row_data)
	return data

def convert_list_to_dataset(list_var, titalize_headers=False, column_order=None, headers_list=None):
	"""
	DESCRIPTION: This function converts list of dictionaries to a dataset
	PARAMETERS: list_var (REQ, list): The list of dictionaries to be converted
				titalize_headers (OPT, bool): True in the case of the ability to get the names of the header in list_var
				column_order (OPT, list): The order of the columns in the dataset
				headers_list (OPT, list): The list of headers to be used in the dataset
	RETURNS: dataset (dataset): The dataset created from the list of dictionaries
	"""
	LOGGER.trace("convert_list_to_dataset(list_var=%s)" % (list_var))
	if not isinstance(list_var, collections.Iterable):
		return list_var

	if headers_list is not None:
		headers = column_names = headers_list
	elif column_order is not None:
		headers = column_names = column_order
	else:
		headers = column_names = list_var[0].keys()
			
	if titalize_headers:
		headers = [name.title() for name in column_names]
		
	
	data = []
	
	for row in list_var:
		row_data = []
		for column in column_names:
			# NOTE: Check to see if key value has a value with styling applied, and only return the value
			if hasattr(row[column], 'value') and hasattr(row[column], 'style'):
				value = str(row[column]['value']) if row[column]['value'] is not None else None
			else:
				value = str(row[column]) if row[column] is not None else None
			row_data.append(value)
		data.append(row_data)
	return system.dataset.toDataSet(headers, data)

def convert_list_to_dataset_free_type(list_var, titalize_headers=False, column_order=None, headers_list=None):
	"""
	DESCRIPTION: This function converts list of dictionaries to a dataset
	PARAMETERS: list_var (REQ, list): The list of dictionaries to be converted
				titalize_headers (OPT, bool): True in the case of the ability to get the names of the header in list_var
	"""
	LOGGER.trace("convert_list_to_dataset(list_var=%s)" % (list_var))
	if not isinstance(list_var, collections.Iterable):
		return list_var

	if headers_list is not None:
		headers = column_names = headers_list
	elif column_order is not None:
		headers = column_names = column_order
	else:
		headers = column_names = list_var[0].keys()
			
	if titalize_headers:
		headers = [name.title() for name in column_names]
		
	
	data = []
	
	for row in list_var:
		row_data = []
		for column in column_names:
			# NOTE: Check to see if key value has a value with styling applied, and only return the value
			if hasattr(row[column], 'value') and hasattr(row[column], 'style'):
				value = row[column]['value'] if row[column]['value'] is not None else None
			else:
				value = row[column]
			row_data.append(value)
		data.append(row_data)
	return system.dataset.toDataSet(headers, data)

def convert_properties_to_dictionary(obj):
	"""
	DESCRIPTION: Converts properties from the view into a dictionary, if possible
	PARAMETERS: obj (REQ, object): The properties to be converted
	RETURNS: dict (dict): The dictionary of the properties
	"""
	LOGGER.trace("convert_properties_to_dictionary(obj=%s)" % (obj))

	if obj is None:
		return None

	# NOTE: If this is a basic qualified value, and not a dictionary with the key 'value', 
	# then replace the object with its value
	if hasattr(obj, 'value') and not hasattr(obj, 'keys'):
		obj = obj.value

	# NOTE: Then check for any kind of dictionary or list
	if hasattr(obj, '__iter__'):
		if hasattr(obj, 'keys'):
			return dict((k, convert_properties_to_dictionary(obj[k])) for k in obj.keys())
		else:
			return list(convert_properties_to_dictionary(x) for x in obj)
	else:
		# anything else
		return obj
	
def convert_from_camel_case_to_title_case(string):
	"""
	DESCRIPTION: Converts a string from camel case to all title case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to title case
	"""
	LOGGER.trace("convert_from_camel_case_to_caps(string=%s)" % (string))
	return re.sub("([a-z])([A-Z])", r"\g<1> \g<2>", string).capitalize()

def convert_from_title_case_to_camel_case(string):
	"""
	DESCRIPTION: Converts a string from title case to camel case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to camel case
	"""
	LOGGER.trace("convert_from_title_case_to_camel_case(string=%s)" % (string))
	return re.sub(r'\W', '', string.title())

def convert_from_camel_case_to_caps(string):
	"""
	DESCRIPTION: Converts a string from camel case to all caps
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to all caps
	"""
	LOGGER.trace("convert_from_camel_case_to_caps(string=%s)" % (string))
	spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", string)
	return spaced.upper()

def convert_from_caps_to_camel_case(string):
	"""
	DESCRIPTION: Converts a string from all caps to camel case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to camel case
	"""
	LOGGER.trace("convert_from_caps_to_camel_case(string=%s)" % (string))
	return re.sub(r'\W', '', string.title())

def convert_from_camel_case_to_snake_case(string):
	"""
	DESCRIPTION: Converts a string from camel case to snake case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to snake case
	"""
	LOGGER.trace("convert_from_camel_case_to_snake_case(string=%s)" % (string))
	pattern = re.compile(r'(?<!^)(?=[A-Z])')
	return pattern.sub('_', string).lower()

def convert_snake_case_to_camel_case(string):	
	"""
	DESCRIPTION: Converts a string from snake case (standard within scripts) to camel case (standard within Ignition props)
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to camel case
	"""
	string = "".join(char.capitalize() for char in string.lower().split("_"))
	return string[0].lower() + string[1:]

def convert_from_camel_case_to_kebab_case(string):
	"""
	DESCRIPTION: Converts a string from camel case to kebab case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to kebab case
	"""
	LOGGER.trace("convert_from_camel_case_to_kebab_case(string=%s)" % (string))
	pattern = re.compile(r'(?<!^)(?=[A-Z])')
	return pattern.sub('-', string).lower()

def convert_kebab_case_to_camel_case(string):
	"""
	DESCRIPTION: Converts a string from kebab case to camel case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to camel case
	"""
	LOGGER.trace("convert_kebab_case_to_camel_case(string=%s)" % (string))
	components = string.split('-')
	return components[0] + ''.join(x.title() for x in components[1:])

def convert_snake_case_to_kebab_case(string):
	"""
	DESCRIPTION: Converts a string from snake case to kebab case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string to kebab case
	"""
	LOGGER.trace("convert_snake_case_to_kebab_case(string=%s)" % (string))
	return string.replace('_', '-')

def convert_to_pascal_case(string):
	"""
	DESCRIPTION: Converts a string to Pascal case (UpperCamelCase)
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string in Pascal case
	"""
	LOGGER.trace("convert_to_pascal_case(string=%s)" % (string))
	camel = convert_snake_case_to_camel_case(string.replace(" ", "_").lower())
	return camel[0].upper() + camel[1:]

def convert_from_pascal_case_to_snake_case(string):
	"""
	DESCRIPTION: Converts a string from Pascal case to snake case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string in snake case
	"""
	LOGGER.trace("convert_from_pascal_case_to_snake_case(string=%s)" % (string))
	pattern = re.compile(r'(?<!^)(?=[A-Z])')
	return pattern.sub('_', string).lower()

def convert_from_kebab_case_to_camel_case(string):
	"""
	DESCRIPTION: Converts a string from kebab case to camel case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string in camel case
	"""
	LOGGER.trace("convert_from_kebab_case_to_camel_case(string=%s)" % (string))
	components = string.split('-')
	return components[0] + ''.join(x.title() for x in components[1:])

def convert_from_sentence_case_to_title_case(string):
	"""
	DESCRIPTION: Converts a string from sentence case to title case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string in title case
	"""
	LOGGER.trace("convert_from_sentence_case_to_title_case(string=%s)" % (string))
	return string.title()

def convert_from_title_case_to_sentence_case(string):
	"""
	DESCRIPTION: Converts a string from title case to sentence case
	PARAMETERS: string (REQ, string): The string to be converted
	RETURNS: string (string): The converted string in sentence case
	"""
	LOGGER.trace("convert_from_title_case_to_sentence_case(string=%s)" % (string))
	return string.capitalize()
	
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

def convert_dict_to_dropdown(options, key_labels=False, titlify=False, sort=True):
	"""
	DESCRIPTION: Creates a list of dictionaries for a dropdown from a dictionary
	PARAMETERS: options (REQ, dict): The dictionary to be converted (key is the label, value is the value)
	"""
	LOGGER.trace("convert_dict_to_dropdown(options=%s)" % (options))
	dropdown_options = []
	
	if key_labels:
		dropdown_options = [{"label": key, "value": val} for key, val in options.iteritems()]
	else:
		dropdown_options = [{"label": val, "value": key} for key, val in options.iteritems()]
	
	if titlify:
		dropdown_options = [{"label": option['label'].title(), "value": option['value']} for option in dropdown_options]
	
	if sort:
		dropdown_options = sorted(dropdown_options, key=lambda option: option['value'])
	
	return dropdown_options

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
