"""
General.Queries
This module contains functions for running named queries.
"""

import java.lang.ClassCastException
import java.lang.Exception
import json

LOGGER = system.util.getLogger("General.Queries")

def run_named_query(path, as_json=True, params={}): # pylint: disable=dangerous-default-value
	"""
	DESCRIPTION: runs a named query provided parameters and a path, returns response in JSON
	PARAMETERS: path (REQ, string): path to the named query to be run
				as_json (OPT, bool): flag for return obj type (True=JSON, False=Dataset)
				params (OPT, dict): parameters for the query to use
	RETURNS: dict: response from the named query or dataset if as_json is False
	"""
	project = system.project.getProjectName()
	try:
		
		try: 
			dataset = system.db.runNamedQuery(path, params)
		except java.lang.ClassCastException: 
			dataset = system.db.runNamedQuery(project, path, params)
		
		if as_json:
			return General.Conversion.convert_dataset_to_list(dataset)
		else:
			return dataset

	except General.Errors.ExceptionWithDetails as e:
		raise e
	except (Exception, java.lang.Exception) as e:
		raise General.Errors.ExceptionWithDetails("Error getting named query at path: %s, with params: %s" 
											% (path, params), LOGGER, e)

def run_scalar_named_query_json(path, params={}): # pylint: disable=dangerous-default-value
	"""
	DESCRIPTION: runs a scalar named query provided parameters and a path, returns response in JSON
	PARAMETERS: path (REQ, string): path to the named query to be run
				as_json (OPT, bool): flag for return obj type (True=JSON, False=Dataset)
				params (OPT, dict): parameters for the query to use
	RETURNS: dict: response in JSON
	"""
	project = system.project.getProjectName()
	try:
		
		try: 
			value = system.db.runNamedQuery(path, params)
		except java.lang.ClassCastException: 
			value = system.db.runNamedQuery(project, path, params)
		if not value:
			return {}
		return convert_unicode_to_str(json.loads(value))
		
	except General.Errors.ExceptionWithDetails as e:
		raise e
	except (Exception, java.lang.Exception) as e:
		raise General.Errors.ExceptionWithDetails("Error getting named query at path: %s, with params: %s"
											% (path, params), LOGGER, e)
	
def convert_unicode_to_str(data):
	"""
	DESCRIPTION: Converts unicode to string
	PARAMETERS: data (REQ, dict): data to convert
	RETURNS: dict: data with unicode converted to string
	"""
	if isinstance(data, dict):
		return {str(key): convert_unicode_to_str(value) for key, value in data.items()}
	elif isinstance(data, list):
		return [convert_unicode_to_str(item) for item in data]
	elif isinstance(data, (unicode, int)):
		return str(data).encode('utf-8')
	else:
		return data
  