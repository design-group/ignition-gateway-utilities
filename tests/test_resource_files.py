"""
DESCRIPTION: Checks to see if each file in script-python directories are included in 
			the resource.json file
"""

import pytest
import os
import json

def test_resource():
	"""
	DESCRIPTION: Checks to see if  Resource.json files exist in every directory with code.py 
	pass if it's present in each
	"""
	ignore = ["__pycache__", ".pyc", "resource.json"]
	path = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir))

	# NOTE: Walk through each directory
	for root_name, dir_names, file_names in os.walk(path): # pylint: disable=unused-variable
		# NOTE: Load the resource.json into an object
		if "resource.json" in file_names:
			with open("%s/resource.json" % root_name) as json_file:
				try:
					resource_data = json.load(json_file)	    
				except: # pylint: disable=bare-except
					pytest.fail('Invalid resource file: %s/resource.json' % (root_name))

			# NOTE: Go through each file in the directory
			for os_file_name in file_names:
				# NOTE: Verify that the file is in the resource.json.files
				if os_file_name not in resource_data.get("files", []) and not any(ignore_text in os_file_name for ignore_text in ignore):
					pytest.fail("%s not found in %s/resource.json" % (os_file_name, root_name))

			# NOTE: Go through each file in the resource.json. files object
			for object_file_name in resource_data.get("files", []):
				# NOTE: Verify that the file is in the directory
				if object_file_name not in file_names and not any(ignore_text in object_file_name for ignore_text in ignore):
					pytest.fail("%s not found in %s" % (object_file_name, root_name))


if __name__ == "__main__":
	pytest.main(["-s", __file__])
