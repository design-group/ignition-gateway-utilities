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
	Description: Returns dataset built from table component
	PARAMETERS:
		table: Table component to get dataset from
	RETURNS: dataset built from table component with proper formatting 
	"""
	table_data = []
	render_list = [column['render'] for column in table.props.columns]
	
	# Add {"column0": value, "column1": value, ...} to represent the column titles
	table_data.append({"column%s" % index: header_title for index, header_title in enumerate(get_column_titles(table))})
	headers = ["column%s" % index for index in range(len(render_list))]
	
	for row in table.props.data:
		temp_dict = {}
		for index, val in enumerate(row.values()):
			if render_list[index] == "date":
				temp_dict.update({"column%s" % index: system.date.format(val, "yy/MM/dd HH:mm:ss")})
			else:
				temp_dict.update({"column%s" % index: round(val, 2)})
		table_data.append(temp_dict)

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
