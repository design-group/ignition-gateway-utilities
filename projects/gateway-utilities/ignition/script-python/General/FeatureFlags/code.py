import ConfigParser, functools
logger = system.util.getLogger("General.FeatureFlags")

try:
	if not hasattr(General, "Files"):
		raise NameError("General.Files not found")
	if not hasattr(General, "Utilities"):
		raise NameError("General.Utilities not found")
except NameError as e:
	logger.warn("Some Features of this script module require other modules, please ensure that each required module is properly loaded or some functionality might not work: %s" % e.message)

FEATURE_FLAG_CONFIG_PATH="data/feature-flags.json"

class FeatureFlagException(Exception):
	pass

class FlagNotFoundException(FeatureFlagException):
	pass


@General.Utilities.execute_on_gateway
def getFeatureFlags(force_refresh=False):
	"""
	DESCRIPTION:
		Get the feature flags from the gateway. If the feature flags have already been
		retrieved, the cached value will be returned unless force_refresh is True.
		If the feature flags have not been retrieved, they will be retrieved and
		cached for future use.
	PARAMETERS: force_refresh (OPT, bool) - Whether to force a refresh of the feature flag config file
	"""

	try:
		feature_flags = General.Files.getGatewayFileContents(FEATURE_FLAG_CONFIG_PATH, force_refresh=force_refresh)
	except General.Files.FileNotFoundException as e:
		# NOTE: The feature flags file is not found, just return an empty object
		feature_flags = {}
		
	if isinstance(feature_flags, str) or isinstance(feature_flags, unicode):
		feature_flags = system.util.jsonDecode(feature_flags) 
	
	return feature_flags

def getFeatureFlagTable(force_refresh=False):
	"""
	DESCRIPTION: Returns the feature flags in a table friendly format
	PARAMETERS: force_refresh (OPT, bool) - Whether to force a refresh of the feature flag config file
	EXAMPLE: [ 
			{ "category_id": "Scripting", "flag_id": "myFeature.newFunction","enabled":true },
			{ "category_id": "UI-Features", "flag_id": "myFeature.UIScreen","enabled":true } 
			]
	"""

	flags = getFeatureFlags(force_refresh=force_refresh)

	feature_flags = []
	for category_id in flags:
		for flag_id in flags[category_id]:
			feature_flags.append({ "category_id": category_id, "flag_id": flag_id, "enabled": flags[category_id][flag_id] })

	return feature_flags

def isFeatureEnabled(category_id, flag_id, force_refresh=False):
	"""
	DESCRIPTION: Checks if a feature flag is enabled
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
			   flag_id (REQ, str) - The flag ID of the feature flag
			   force_refresh (OPT, bool) - Whether to force a refresh of the feature flag config file
	"""

	flags = getFeatureFlags(force_refresh=force_refresh)
	
	if category_id not in flags:
		raise FeatureFlagException("Feature flag category not found: %s" % category_id)
	
	flag_category = flags[category_id]
	
	if flag_id not in flag_category:
		raise FeatureFlagException("Feature flag not found in category: %s - %s" % (category_id, flag_id))

	return flag_category[flag_id]

def ifEnabled(category_id, flag_id, old_func=None):
	"""
	DESCRIPTION: Decorator for feature flags
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
				flag_id (REQ, str) - The flag ID of the feature flag
	EXAMPLE: Can be used to decorate a scripting function with the following syntax
		@General.FeatureFlags.ifEnabled("myCategory", "myFeature")
			def myFunction ... 
	"""
	def flag_wrapper(func):
		def wrapper(*args,**kwargs):
			if isFeatureEnabled(category_id, flag_id) == True:
				return func(*args, **kwargs)
			elif old_func is not None:
				return old_func(*args, **kwargs)
				
		return wrapper
	return flag_wrapper
	
def setFeatureFlag(category_id, flag_id, enabled):
	"""
	DESCRIPTION: Sets a feature flag
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
			   flag_id (REQ, str) - The flag ID of the feature flag
			   enabled (REQ, bool) - The enabled/disabled setting of the feature flag
	"""

	flags = getFeatureFlags(force_refresh=True)
	
	if category_id not in flags:
		flags[category_id] = {}
	
	flag_category = flags[category_id]
	
	flag_category[flag_id] = enabled

	General.Files.setGatewayFileContents(FEATURE_FLAG_CONFIG_PATH, flags)

def deleteFeatureFlag(category_id, flag_id):
	"""
	DESCRIPTION: Deletes a feature flag
	PARAMETERS category_id (REQ, str) - The category ID of the feature flag
			   flag_id (REQ, str) - The flag ID of the feature flag
	"""

	flags = getFeatureFlags(force_refresh=True)
	
	if category_id not in flags:
		raise FlagNotFoundException("Feature flag category not found: %s" % category_id)
	
	flag_category = flags[category_id]
	
	if flag_id not in flag_category:
		raise FeatureFlagException("Feature flag not found in category: %s - %s" % (category_id, flag_id))

	del flag_category[flag_id]

	# Verify that the category is not empty, and if so, delete it
	if len(flag_category) == 0:
		del flags[category_id]

	General.Files.setGatewayFileContents(FEATURE_FLAG_CONFIG_PATH, flags)