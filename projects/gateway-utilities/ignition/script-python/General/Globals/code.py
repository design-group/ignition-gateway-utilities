"""
General.Globals

Stores global variables for the project

"""

def get_global_key(key):
	"""
	DESCRIPTION: Gets the global key from the ignition globals
	PARAMETERS: key (REQ, str) - The key to get from the globals
	
	"""
	ignition_globals = system.util.getGlobals()
	ignition_globals.setdefault(key, {})
	return ignition_globals[key]


def set_global_key(key, data, cache_time=5):
	ignition_globals = system.util.getGlobals()
	ignition_globals.setdefault(key, {})
	expiration_ms = system.date.toMillis(system.date.addMinutes(system.date.now(), cache_time))
	ignition_globals[key] = {
			"data": data,
			"expiration": expiration_ms
		}
	return ignition_globals[key]