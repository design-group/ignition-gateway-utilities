import os
logger = system.util.getLogger("GatewayFileContents")

try:
	if not hasattr(General, "Utilities"):
		raise NameError("General.Utilities not found")
except NameError as e:
	logger.warn("Some Features of this script module require other modules, please ensure that each required module is properly loaded or some functionality might not work: %s" % e.message)

'''
This script leverages a gateway message handler, called "executeInGatewayScope". The purpose of this message handler takes any calls made in the client scope, and moves them over to the gateway. That way when files are read, they come off the gateway file system and not the local development environment.

That message handler should take the following arguments: 
	func (REQ, str) - The fully qualified path of a function in the designated project
	kwargs (OPT, dict) - A dictionary containing the key-value pairs that match up to the functions keyword arguments

The definition of the "executeInGatewayScope" function is as follows:

def handleMessage(payload):
	"""
	This message handler will be called each time a message of this
	type is received.

	Arguments:
		payload: A dictionary that holds the objects passed to this
			 message handler. Retrieve them with a subscript, e.g.
			 myObject = payload['argumentName']
	"""
	
	"""
	Example call in project scope: 
		system.util.sendRequest(project, "executeInGatewayScope", {"func":"myScript.myFunction", 'kwargs':{"myParam1":123,"myParam2":456}}), 
	"""
	
	if payload.get('func') is None:
		raise TypeError("executeInGatewayScope expects a payload object named func")
	
	func_reference = eval(payload['func'])
	args = payload.get('args', [])
	kwargs = payload.get('kwargs', {})
	
	return func_reference(*args, **kwargs)

'''

ignition_globals = system.util.getGlobals()

# NOTE: This key is the key inside the globals that gateway-files are stored in
GATEWAY_FILES_KEY="gateway-files"
ignition_globals.setdefault(GATEWAY_FILES_KEY, {})

class GatewayFileException(Exception):
	pass
	
class FileNotFoundException(GatewayFileException):
	pass

def readJsonFile(file_path):
	"""
	DESCRIPTION: Json parser that will automatically read a json file and return it as a python object
	PARAMETERS: file_path (REQ, str) - The file path to the desired file, from the ignition directory
	"""
	try:
		return system.util.jsonDecode(system.file.readFileAsString(file_path))
	except:
		# NOTE: I do not use an exception here, because the java exception is not raised in a way that is caught by it
		raise GatewayFileException("Error loading %s, not a valid JSON dictionary" % file_path)


file_readers = {
	".json": readJsonFile,
}

# NOTE: If we ar enot executing in the gateway scope, then file paths will be relative to the client which we dont want. Sending a request to the gateway will allow it to read gateway files 
@General.Utilities.execute_on_gateway
def getGatewayFileContents(file_path, force_refresh=False, store_in_globals=True, read_file_as_bytes=False):
	
	if not os.path.exists(file_path):
		raise FileNotFoundException("Unable to find gateway file at %s" % (file_path))
	
	# NOTE: Extract the file type to make sure we can load it correctly
	file_type = os.path.splitext(file_path)[-1]
	
	
	# NOTE: If at some point we failed to load the file and its blank, lets force it to reload
	if not ignition_globals.get(GATEWAY_FILES_KEY, {}).get(file_path, {}).get('data'):
		force_refresh = True
	
	# NOTE: Check if the last modification time is newer than the last time we imported the file
	if os.path.getmtime(file_path) > ignition_globals.get(GATEWAY_FILES_KEY, {}).get(file_path, {}).get('lastModifiedTime', 0) or force_refresh:
		file_reader = file_readers.get(file_type)
		
		if not file_reader and not read_file_as_bytes:
			raise GatewayFileException("Unable to load file of type: %s, no reader defined" % file_type)
		
		if read_file_as_bytes:
			file_contents = system.file.readFileAsBytes(file_path)
		else:
			file_contents = file_reader(file_path)
		
		# NOTE: If we dont want to store this file in the globals for some reason, then we should just return it
		if not store_in_globals:
			return file_contents
			
		# NOTE: Set the reference in the globals to the new data
		ignition_globals[GATEWAY_FILES_KEY][file_path] = {
								'data': file_contents, 
								'lastModifiedTime': os.path.getmtime(file_path)
								}
															
		logger.info("Updating Gateway File in Cache: %s" % file_path)
	
	# NOTE: Regardless of if we updated the data, return it anyway
	return ignition_globals[GATEWAY_FILES_KEY][file_path]['data']

@General.Utilities.execute_on_gateway
def setGatewayFileContents(file_path, file_data, store_in_globals=True):
	"""
	DESCRIPTION: Sets the contents of a file on the gateway
	PARAMETERS: file_path (REQ, str) - The file path to the desired file, from the ignition directory
				file_data (REQ, str) - The data to write to the file
				store_in_globals (OPT, bool) - If we should store the file in the globals cache
	"""
	# NOTE: Check to verify that file file_data is a string, else try to convert json
	if not isinstance(file_data, str):
		try:
			file_data = system.util.jsonEncode(file_data)
		except:
			raise GatewayFileException("Unable to convert file_data to json")

	system.file.writeFile(file_path, file_data)
	
	# NOTE: If we dont want to store this file in the globals for some reason, then we should just return it
	if not store_in_globals:
		return 
		
	# NOTE: Set the reference in the globals to the new data
	ignition_globals[GATEWAY_FILES_KEY][file_path] = {
							'data': file_data, 
							'lastModifiedTime': os.path.getmtime(file_path)
							}
	logger.info("Updating Gateway File in Cache: %s" % file_path)					
	return 
