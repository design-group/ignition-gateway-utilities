"""
General.FeatureFlags

This module provides a way to enable/disable features in Ignition.
This is useful for testing new features or hiding features that are not yet ready for production.

"""
import General.Files
import General.Utilities

LOGGER = system.util.getLogger("General.FeatureFlags")
FEATURE_FLAG_CONFIG_PATH = "data/feature-flags.json"

class FeatureFlagException(Exception):
	"""
	DESCRIPTION: Base Exception class for FeatureFlag
	"""

class FlagNotFoundException(FeatureFlagException):
	"""
	DESCRIPTION: Exception class for when a flag is not found
	"""

@General.Utilities.execute_on_gateway
def get_feature_flags(force_refresh=False):
	"""
	DESCRIPTION:
		Get the feature flags from the gateway. If the feature flags have already been
		retrieved, the cached value will be returned unless force_refresh is True.
		If the feature flags have not been retrieved, they will be retrieved and
		cached for future use.
	PARAMETERS: force_refresh (OPT, bool) - Whether to force a refresh of the feature flag config file
	"""

	try:
		feature_flags = General.Files.get_gateway_file_contents(
														FEATURE_FLAG_CONFIG_PATH,
														force_refresh=force_refresh
													)
	except General.Files.FileNotFoundException:
		# NOTE: The feature flags file is not found, just return an empty object
		feature_flags = {}

	if isinstance(feature_flags, (str, unicode)):
		feature_flags = system.util.jsonDecode(feature_flags)

	return feature_flags

def get_feature_flag_table(force_refresh=False):
	"""
	DESCRIPTION: Returns the feature flags in a table friendly format
	PARAMETERS: force_refresh (OPT, bool) - Whether to force a refresh of the feature flag config file
	EXAMPLE: [
			{ "category_id": "Scripting", "flag_id": "myFeature.newFunction","enabled":true },
			{ "category_id": "UI-Features", "flag_id": "myFeature.UIScreen","enabled":true }
			]
	"""

	flags = get_feature_flags(force_refresh=force_refresh)

	feature_flags = []
	for category_id in flags:
		for flag_id in flags[category_id]:
			feature_flags.append({
							"category_id": category_id,
							"flag_id": flag_id,
							"enabled": flags[category_id][flag_id]
						})

	return feature_flags

def is_feature_enabled(category_id, flag_id, force_refresh=False):
	"""
	DESCRIPTION: Checks if a feature flag is enabled
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
			   flag_id (REQ, str) - The flag ID of the feature flag
			   force_refresh (OPT, bool) - Whether to force a refresh of the feature flag config file
	"""

	flags = get_feature_flags(force_refresh=force_refresh)

	if category_id not in flags:
		raise FeatureFlagException("Feature flag category not found: %s" % category_id)

	flag_category = flags[category_id]

	if flag_id not in flag_category:
		raise FeatureFlagException("Feature flag not found in category: %s - %s" % (category_id, flag_id))

	return flag_category[flag_id]

def if_enabled(category_id, flag_id, old_func=None):
	"""
	DESCRIPTION: Decorator for feature flags
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
				flag_id (REQ, str) - The flag ID of the feature flag
	EXAMPLE: Can be used to decorate a scripting function with the following syntax
		@General.FeatureFlags.if_enabled("myCategory", "myFeature")
			def myFunction ...
	"""
	def flag_wrapper(func):
		"""
		DESCRIPTION: Wrapper function for the decorator,
					this is what allows us to add args and kwargs to the function
		"""
		def wrapper(*args, **kwargs):
			"""
			DESCRIPTION: This wrapper function is how the decorator is actually applied to the function
			"""
			if is_feature_enabled(category_id, flag_id) is True:
				return func(*args, **kwargs)
			elif old_func is not None:
				return old_func(*args, **kwargs)
				
			return None

		return wrapper
	return flag_wrapper

def set_feature_flag(category_id, flag_id, enabled):
	"""
	DESCRIPTION: Sets a feature flag
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
			   flag_id (REQ, str) - The flag ID of the feature flag
			   enabled (REQ, bool) - The enabled/disabled setting of the feature flag
	"""

	flags = get_feature_flags(force_refresh=True)

	if category_id not in flags:
		flags[category_id] = {}

	flag_category = flags[category_id]

	flag_category[flag_id] = enabled

	General.Files.set_gateway_file_contents(FEATURE_FLAG_CONFIG_PATH, flags)

def delete_feature_flag(category_id, flag_id):
	"""
	DESCRIPTION: Deletes a feature flag
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
			   flag_id (REQ, str) - The flag ID of the feature flag
	"""

	flags = get_feature_flags(force_refresh=True)

	if category_id not in flags:
		raise FlagNotFoundException("Feature flag category not found: %s" % category_id)

	flag_category = flags[category_id]

	if flag_id not in flag_category:
		raise FeatureFlagException("Feature flag not found in category: %s - %s" % (category_id, flag_id))

	del flag_category[flag_id]

	# Verify that the category is not empty, and if so, delete it
	if not flag_category:
		del flags[category_id]

	General.Files.set_gateway_file_contents(FEATURE_FLAG_CONFIG_PATH, flags)
