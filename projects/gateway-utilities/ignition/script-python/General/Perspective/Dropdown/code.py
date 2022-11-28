"""
General.Perspective.Dropdown

This script contains functions used with dropdown list components.
"""

def build_tag_dropdown(base_path=""):
	"""
	DESCRIPTION: Builds a dropdown list based off of a specified base path 
				If no path is provided, the top level tag providers will be searched.
	PARAMETERS: base_path (OPT, str) - The base path to search for tags
	RETURNS: List of objects being returned by getOption() on each tag provider
	""" 
	tags = system.tag.getConfiguration(base_path)
	tag_list = [str(tag['path']) for tag in tags]
	return [{"value": tag_path, "label": tag_path.replace('[', '').replace(']', '')} for tag_path in tag_list]
	