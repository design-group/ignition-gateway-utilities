"""
General.Config

This module provides functions for retrieving configuration files from the gateway.
"""
import General.Files
import General.Utilities

LOGGER = system.util.getLogger("General.Config")
CONFIG_SOURCE_DIRECTORY = "data/configs/"


class ConfigException(Exception):
	"""
	DESCRIPTION: Exception class for Config module
	"""

def get_config_value(config_name, config_key=None, force_refresh=False):
	"""
	DESCRIPTION: Get the value of a specific key in a config file
	PARAMETERS: config_name (REQ, str) - the name of the config file to be retrieved,
									unincluding extension.
				config_key (REQ, str) - the key to retrieve from the config file
									(if omitted, the entire thresholds file is returned)
				force_refresh (OPT, bool) - force a refresh of the config file
	RETURNS: String - the value of the key in the config file
	"""

	file_path = '%s/%s.json' % (CONFIG_SOURCE_DIRECTORY, config_name)

	config = General.Files.get_gateway_file_contents(file_path, force_refresh=force_refresh)

	if config_key is None:
		return config

	return General.Utilities.read_json_path(config, config_key)
