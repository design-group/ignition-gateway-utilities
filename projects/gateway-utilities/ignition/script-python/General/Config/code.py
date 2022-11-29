"""
General.Config

This module provides functions for retrieving configuration files from the gateway.
"""
import General.Files
import General.Utilities

#LOGGER = system.util.getLogger("General.Config")
CONFIG_SOURCE_DIRECTORY = "data/configs/"
logger = General.Logging.Logger("General.Config")

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
	"""

	file_path = '%s/%s.json' % (CONFIG_SOURCE_DIRECTORY, config_name)

	config = General.Files.get_gateway_file_contents(file_path, force_refresh=force_refresh)

	if config_key is None:
		return config

	return General.Utilities.read_json_path(config, config_key)

def set_config_value(config_name, config_key, config_value):
	"""
	DESCRIPTION: Set the value of a specific key in a config file
	PARAMETERS: config_name (REQ, str) - the name of the config file to be retrieved,
									unincluding extension.
				config_key (REQ, str) - the key to retrieve from the config file
				config_value (REQ, str) - the value to set
	"""

	file_path = '%s/%s.json' % (CONFIG_SOURCE_DIRECTORY, config_name)

	config = General.Files.get_gateway_file_contents(file_path)
	
	logger.info("Config contents %s" % config)

	new_config = General.Utilities.write_json_path(config, config_key, config_value)

	logger.info("New Config contents %s" % new_config)
	General.Files.set_gateway_file_contents(file_path, new_config)