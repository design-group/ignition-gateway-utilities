"""
General.Conversion

This module contains functions for converting data types.

This module should not have any dependencies on any other Ignition modules.
"""

logger = system.util.getLogger("General.Conversion")

import re, collections

def convert_dataset_to_list(dataset, strip_values=False):
	"""
	DESCRIPTION: This function converts a dataset to a list of dictionaries 
	PARAMETERS: dataset (REQ, dataset): The dataset to be converted to a list of dictionaries
	"""
	logger.trace("General.Conversion.convert_dataset_to_list(dataset=%s)" % (dataset))

	try: 
		columnNames = dataset.getColumnNames()
	except:			
		return dataset	

	data = []
	
	for row in range(dataset.getRowCount()):
		rowData = {}
		for column in range(dataset.getColumnCount()):
			rowData[columnNames[column]] = dataset.getValueAt(row, column)
		data.append(rowData)
	return data
	

def convert_list_to_dataset(listVar, titalize_headers=False, columnOrder=None):
	"""
	DESCRIPTION: This function converts list of dictionaries to a dataset
	PARAMETERS: listVar (REQ, list): The list of dictionaries to be converted
				titalize_headers (OPT, bool): True in the case of the ability to get the names of the header in listVar
	"""
	logger.trace("General.Conversion.convert_list_to_dataset(listVar=%s)" % (listVar))

	try: 
		if columnOrder is not None:
			headers = columnNames = columnOrder
		else:
			headers = columnNames = listVar[0].keys()
				
		if titalize_headers:
			headers = [name.title() for name in columnNames]
	except:
		return listVar		
	
	data = []
	
	for row in listVar:
		rowData = []
		for column in columnNames:
			# NOTE: Check to see if key value has a value with styling applied, and only return the value
			if hasattr(row[column], 'value') and hasattr(row[column], 'style'):
				value = str(row[column]['value']) if row[column]['value'] is not None else None
			else:
				value = str(row[column]) if row[column] is not None else None
			rowData.append(value)
		data.append(rowData)
	
	return system.dataset.toDataSet(headers, data)
	

def convert_properties_to_dictionary(obj):
	"""
	DESCRIPTION: Converts properties from the view into a dictionary, if possible
	PARAMETERS: obj (REQ, object): The properties to be converted
	"""
	logger.trace("General.Conversion.convert_properties_to_dictionary(obj=%s)" % (obj))
	badVariable = None
	try:
		if obj is None:
			return None

		# NOTE: If this is a basic qualified value, and not a dictionary with the key 'value', then replace the object with its value
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

	except Exception as e:
		logger.error("Error converting: %s - %s" (obj, e))
		return badVariable
	
def convert_from_camel_case_to_caps(string):
	"""
	DESCRIPTION: Converts a string from camel case to all caps
	PARAMETERS: string (REQ, string): The string to be converted
	"""
	logger.trace("General.Conversion.convert_from_camel_case_to_caps(string=%s)" % (string))
	return re.sub("([a-z])([A-Z])","\g<1> \g<2>",string).capitalize()
	
def convert_list_to_dropdown(options):
	"""
	DESCRIPTION: Creates a list of dictionaries for each object to allow for a dropdown option
	PARAMETERS: options (REQ, list): The list of values possible for a drop down
	"""
	logger.trace("General.Conversion.convert_list_to_dropdown(options=%s)" % (options))
	dropdownOptions = []
	for option in options:
		if isinstance(option, basestring):
			dropdownOptions.append({"label": option, "value": option})
		elif isinstance(option, collections.Mapping):
			dropdownOptions.append(option)
	return dropdownOptions

def convert_dict_to_dropdown(options):
	"""
	DESCRIPTION: Creates a list of dictionaries for a dropdown from a dictionary
	PARAMETERS: options (REQ, dict): The dictionary to be converted (key is the label, value is the value)
	"""
	logger.trace("General.Conversion.convert_dict_to_dropdown(options=%s)" % (options))
	dropdownOptions = []
	for key in options.keys():
		dropdownOptions.append({"label": options[key], "value": key})
	return sorted(dropdownOptions, key=lambda opt: opt['value'])
