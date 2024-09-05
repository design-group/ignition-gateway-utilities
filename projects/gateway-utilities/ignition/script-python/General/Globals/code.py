"""
General.Globals

Stores global variables for the project

"""

def get_global_key(key):
	"""
	DESCRIPTION: Gets the global key from the ignition globals
	PARAMETERS: key (REQ, str) - The key to get from the globals
	RETURNS: dict - The data stored in the globals
	"""
	ignition_globals = system.util.getGlobals()
	ignition_globals.setdefault(key, {})
	return ignition_globals[key]


def set_global_key(key, data, cache_time=5):
	"""
	DESCRIPTION: Sets the global key in the ignition globals
	PARAMETERS: key (REQ, str) - The key to set in the globals
				data (REQ, dict) - The data to store in the globals
				cache_time (OPT, int) - The time in minutes to store the data in the globals
	RETURNS: dict - The data stored in the globals
	"""
	ignition_globals = system.util.getGlobals()
	ignition_globals.setdefault(key, {})
	expiration_ms = system.date.toMillis(system.date.addMinutes(system.date.now(), cache_time))
	ignition_globals[key] = {
			"data": data,
			"expiration": expiration_ms
		}
	return ignition_globals[key]
