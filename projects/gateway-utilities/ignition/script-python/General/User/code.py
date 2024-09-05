"""
	General.User
	
	DESCRIPTION: All queries related to user data
"""

import json

LOGGER = system.util.getLogger("General.User")
USER_PREFERENCES_KEY = 'userPreferences'

def get_username_for_session(session):
	"""
	DESCRIPTION: Get user object for the session
	PARAMETERS: session (SessionScriptWrapper) : Session object
	RETURNS: User object
	"""
	return session.props.auth.user.userName

def get_preferences_from_session(session):
	"""
	DESCRIPTION: Get user preferences from session
	PARAMETERS: session (SessionScriptWrapper) : Session object
	RETURNS: Dict of user preferences
	"""
	return General.Conversion.convert_properties_to_dictionary(session.custom.get(USER_PREFERENCES_KEY, {}))

def get_user_preferences(username):
	"""
	DESCRIPTION: Get user preferences
	PARAMETERS: username (str) : Name of the user to be returned
	RETURNS: Dict of user preferences
	"""	
	query_path = 'User/Preferences/SELECT/Get User Pref'
	params = {'userName': username}
	result = General.Queries.run_named_query(query_path, params=params)
	return json.loads(result)	

def set_user_preferences(username, user_preferences):
	"""
	DESCRIPTION: Set user preferences
	PARAMETERS: username (str) : Name of the user to be returned
				user_preferences (dict) : User preferences to be stored in the database
	RETURNS: None
	Raises: TypeError if user_preferences is a string
	"""
	if isinstance(user_preferences, (unicode, str)):
		raise TypeError("user_preferences must be a dictionary, not a string")

	query_path = "User/Preferences/UPDATE/Set User Pref"
	user_preferences = General.Conversion.convert_properties_to_dictionary(user_preferences)
	params = {'userName': username, 'userSettings': system.util.jsonEncode(user_preferences)}
	General.Queries.run_named_query(query_path, params=params)

def set_user_preference_value(session, preference_name, preference_value):
	"""
	DESCRIPTION: Set user preferences
	PARAMETERS: session (SessionScriptWrapper) : Session object
				preference_name (str) : Name of the preference to be set
				preference_value (str) : Value of the preference to be set
	RETURNS: None
	"""
	preferences = get_preferences_from_session(session)
	
	if preferences.get(preference_name) == preference_value:
		return
 
	preferences[preference_name] = preference_value
	set_user_preferences(get_username_for_session(session), preferences)
	session.refreshBinding('custom.%s' % USER_PREFERENCES_KEY)
