"""
General.Perspective.Table

This script contains functions used with table components.
"""
import General.Conversion

def export_table_to_xlsx(table):
	"""
	DESCRIPTION: Exports the table to an xlsx file
	PARAMETERS:
		table: Table object being exported
	RETURNS: 
	"""
	table_dataset = get_dataset(table)
	excel_data = system.dataset.toExcel(showHeaders=True, dataset=table_dataset)
	system.perspective.download("data.xlsx", excel_data)

def export_table_to_csv(table):
	"""
	DESCRIPTION: Exports the table to a CSV file
	PARAMETERS:
		table: Table object being exported
	RETURNS: 
	"""
	table_dataset = get_dataset(table)
	csv_data = system.dataset.toCSV(showHeaders=True, dataset=table_dataset)
	system.perspective.download("data.csv", csv_data)

def get_dataset(table):
	"""
	DESCRIPTION: Generates a dataset from a table component with formatted headers.
	PARAMETERS: 
		table (REQ, Table): The table component to get the dataset from. 
			It should contain properties `props.columns` and `props.data`.
	RETURNS: 
		dataset (Dataset): A dataset object created from the table component with headers in uppercase,
			formatted according to the given logic.
	"""
	table_data = []

	headers = [str(column.field) for column in table.props.columns if column.get('visible', True)]
	replaced_headers = {
		str(column.field):str(column.header.title) for column in table.props.columns if column.header.title != ""
	}

	for row in table.props.data:
		temp_dict = {}
		for key, val in row.items():
			if key in replaced_headers:
				key_name = replaced_headers[key]
			else:
				key_name = key
			
			key_name = str(key_name).upper()
			temp_dict[key_name] = val

		table_data.append(temp_dict)
	
	for index, header in enumerate(headers):
		if header in replaced_headers:
			headers[index] = replaced_headers[header].upper()
		else:
			headers[index] = header.upper()

	return General.Conversion.convert_list_to_dataset(list_var=table_data, headers_list=headers)

def get_column_template(field, title, datatype):
	"""
	DESCRIPTION: Sets the attributes of the columns
	PARAMETERS:
		field: original value to look for when populating the data
		title: name being shown in column
		datatype: data type for this object
	RETURNS: dictionary of attributes on the column
	"""
	return {
	  "field": field,
	  "visible": True,
	  "editable": False,
	  "render": datatype,
	  "justify": "auto",
	  "align": "center",
	  "resizable": True,
	  "sortable": True,
	  "sort": "none",
	  "viewPath": "",
	  "viewParams": {},
	  "boolean": "checkbox",
	  "number": "value",
	  "numberFormat": "0,0.##",
	  "dateFormat": "MM/DD/YYYY",
	  "width": "",
	  "strictWidth": False,
	  "style": {
	    "classes": ""
	  },
	  "header": {
	    "title": title,
	    "justify": "center",
	    "align": "center",
	    "style": {
	      "classes": ""
	    }
	  }
	}
	
def get_column_titles(table):
	"""
	DESCRIPTION: Returns a list of column title names
	PARAMETERS:
		table_component: Table component to get column titles from
	RETURNS: list of column titles
	"""
	columns = table.props.columns
	column_titles = []
	for column in columns:
		column_titles.append(column['header']['title'])
	return column_titles
