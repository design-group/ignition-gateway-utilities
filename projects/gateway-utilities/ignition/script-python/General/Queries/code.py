"""
General.Queries
This module contains functions for running named queries.
"""

import java.lang.ClassCastException
import java.lang.Exception
import json

LOGGER = system.util.getLogger("General.Queries")

def run_named_query(path, as_json=True, params=None):
	"""
	DESCRIPTION: runs a named query provided parameters and a path, returns response in JSON
	PARAMETERS: path (REQ, string): path to the named query to be run
				as_json (OPT, bool): flag for return obj type (True=JSON, False=Dataset)
				params (OPT, dict): parameters for the query to use
	RETURNS: dict: response from the named query or dataset if as_json is False
	"""
	project = system.project.getProjectName()
	params = {} if not params else params
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

def run_scalar_named_query_json(path, params=None):
	"""
	DESCRIPTION: runs a scalar named query provided parameters and a path, returns response in JSON
	PARAMETERS: path (REQ, string): path to the named query to be run
				as_json (OPT, bool): flag for return obj type (True=JSON, False=Dataset)
				params (OPT, dict): parameters for the query to use
	RETURNS: dict: response in JSON
	"""
	project = system.project.getProjectName()
	params = {} if not params else params
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
  
def get_query_filter(filter_dict, include_where=True, acceptable_filter_columns=None):
	"""
	DESCRIPTION: Builds a query string based on the provided filter dictionary
	PARAMETERS: filter_dict (REQ, dict): A dictionary containing the filter conditions
				include_where (OPT, bool): A flag to include the WHERE keyword in the query string
	RETURNS: query_string (string): The query string built from the filter dictionary

	EXAMPLE:
		path = "path/to/query"
		# NOTE: In this example, the query was 'SELECT * FROM table_name {filtering_string}'

		filters = {
			"column_name": [
				"23-00012",
				"23-00013",
				"23-00014"
			],
			"column_name": 99999,
			"column_name": "WhatYouWantItToBe"
			"column_name": {
				"OR": [12345, 99999]
			},
			"column_name": {
				"NOT": "WhatYouDontWantItToBe"
			},
			"column_name": {
				">": 50
			}
		}

		return General.Queries.run_filtered_query(path, filter_dict=filters)

	"""
	try:
		filter_columns = ["row_filter"]
		if acceptable_filter_columns is None:
			filter_columns += [key for key in filter_dict.keys()]
		else:
			filter_columns += acceptable_filter_columns
		filter_dict = {key: value for key, value in filter_dict.iteritems() if key in filter_columns}
		# Initialize empty lists to store the query string conditions
		and_conditions = []
		or_conditions = []
		not_conditions = []
		
		# Build the filter conditions based on the provided filter dictionary
		for column_name, value in filter_dict.iteritems():
			if isinstance(value, dict):
				if "OR" in value:
					or_values = value['OR']
					or_clause = []
					for or_value in or_values:
						or_condition = build_condition(column_name, or_value)
						or_clause.append(or_condition)
					or_conditions.append("(" + " OR ".join(or_clause) + ")")
				elif "NOT" in value:
					not_value = value['NOT']
					not_condition = build_condition(column_name, not_value, negate=True)
					not_conditions.append(not_condition)
				elif "IN" in value:
					in_value = value['IN']
					condition = build_condition(column_name, in_value)
					and_conditions.append(condition)
				else:
					# Handle comparison operators
					condition = build_condition(column_name, value)
					and_conditions.append(condition)
			else:
				condition = build_condition(column_name, value)
				and_conditions.append(condition)
		
		# Build the query string
		query_string_parts = []
		if include_where:
			query_string_parts.append("WHERE 1 = 1")

		if and_conditions:
			query_string_parts.append("AND")
			query_string_parts.append(" AND ".join(and_conditions))

		if or_conditions:
			query_string_parts.append("AND")
			query_string_parts.append(" AND ".join(or_conditions))

		if not_conditions:
			query_string_parts.append("AND")
			query_string_parts.append(" AND ".join(not_conditions))

		query_string = " ".join(query_string_parts)
		return query_string

	except Exception as e:
		raise General.Errors.ExceptionWithDetails("Error building query filter", LOGGER, e)

def build_condition(column_name, value, negate=False):
	"""
	DESCRIPTION: Builds a condition string for a column name and value
	PARAMETERS: column_name (REQ, string): The name of the column to filter on
				value (REQ, mixed): The value to filter on
				negate (OPT, bool): A flag to negate the condition
	RETURNS: condition (string): The condition string built from the column name and value
	"""
	try:
		if isinstance(value, dict):
			# Check for operator keys in the dictionary
			if '>' in value:
				condition = "%s > %s" % (column_name, value['>'])
			elif '<' in value:
				condition = "%s < %s" % (column_name, value['<'])
			elif '>=' in value:
				condition = "%s >= %s" % (column_name, value['>='])
			elif '<=' in value:
				condition = "%s <= %s" % (column_name, value['<='])
			else:
				raise Exception("Invalid operator in filter dictionary for column %s: %s" % (column_name, value))
		elif column_name.lower() == 'row_filter':
			condition = "lower(row_to_json(results.*)::text) LIKE '%%%s%%'" % value.lower()
		elif isinstance(value, list):
			if all(isinstance(item, (int, float, long)) for item in value):
				placeholders = ",".join(str(item) for item in value)
				condition = "%s IN (%s)" % (column_name, placeholders)
			else:
				placeholders = "','".join(value)
				condition = "%s IN ('%s')" % (column_name, placeholders)
		elif isinstance(value, (str, unicode)) and '*' in value:
			condition = "%s LIKE '%s'" % (column_name, value.replace('*', '%'))
		elif isinstance(value, (str, unicode)):
			condition = "%s = '%s'" % (column_name, value)
		elif isinstance(value, (int, float, long)):
			condition = "%s = %s" % (column_name, value)
		else:
			raise Exception("Invalid filter value type %s for column %s: %s" % (type(value), column_name, value))

		if negate:
			condition = "NOT " + condition

		return condition

	except Exception as e:
		raise General.Errors.ExceptionWithDetails("Error building condition for column %s with value %s" % (column_name, value), LOGGER, e)

def run_filtered_query(path, params=None, filter_dict=None, offset=0, limit=25, acceptable_filter_columns=None, include_where=True):
	"""
	DESCRIPTION: Runs a named query with a filter dictionary
	PARAMETERS: path (REQ, string): path to the named query to be run
				params (OPT, dict): parameters for the query to use
				filter_dict (OPT, dict): dictionary of filter conditions
				offset (OPT, int): offset for the query
				limit (OPT, int): limit for the query
				acceptable_filter_columns (OPT, list): list of acceptable filter columns
				include_where (OPT, bool): flag to include the WHERE keyword in the query string
	RETURNS: dict: response from the named query
	"""
	if filter_dict is None:
		filter_dict = {}

	if params is None:
		params = {}
  
	if acceptable_filter_columns is None:
		acceptable_filter_columns = []
	query_string = General.Queries.get_query_filter(filter_dict=filter_dict, include_where=include_where, acceptable_filter_columns=acceptable_filter_columns)
	query_string += " LIMIT %s OFFSET %s" % (limit, offset)
	params["filtering_string"] = query_string
	return General.Queries.run_named_query(path, params=params)
