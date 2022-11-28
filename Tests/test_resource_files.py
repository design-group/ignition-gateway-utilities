import pytest, os, json

def test_resource():
    """
    DESCRIPTION: Checks to see if  Resource.json files exist in every directory with code.py 
    pass if it's present in each
    """
    ignore = ["__pycache__", ".pyc", "resource.json"]
    path = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir))

    # NOTE: Walk through each directory
    for root_name, dir_names, file_names in os.walk(path):
        # NOTE: Load the resource.json into an object
        if 'resource.json' in file_names:
            with open("%s/resource.json" % root_name) as json_file:
                resource_data = json.load(json_file)

            # NOTE: Go through each file in the directory
            for file in file_names:
                # NOTE: Verify that the file is in the resource.json.files
                if file not in resource_data.get('files', []) and not any(ignore_text in file for ignore_text in  ignore):
                    pytest.fail('%s not found in %s/resource.json' % (file, root_name))

if __name__ == "__main__":
	pytest.main(["-s", __file__])