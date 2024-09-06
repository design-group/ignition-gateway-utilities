"""
General.Serialization
This module contains functions for serializing and deserializing objects in Ignition.
"""

LOGGER = system.util.getLogger("General.Serialization")

def serialize_to_dict(obj):
	"""
	DESCRIPTION: This function serializes an object to a dictionary.
	PARAMETERS: obj (REQ, object) - The object to serialize
	RETURNS: dict - The serialized object
	"""
	if isinstance(obj, (bool, int, long, float, str, unicode)):
		return obj
	elif isinstance(obj, (list, tuple)):
		return [serialize_to_dict(item) for item in obj]
	elif isinstance(obj, dict):
		return {str(key): serialize_to_dict(value) for key, value in obj.items()}
	elif obj is None:
		return None
	else:
		# Assume it's a custom classs
		attributes = {}
		for attr_name in dir(obj):
			# Ignore methods, private attributes, and abstract attributes
			if not attr_name.startswith('__') and not attr_name.startswith('_abc_') and not attr_name.startswith('_'):
				attr_value = getattr(obj, attr_name)
				if not callable(attr_value):
					attributes[attr_name] = serialize_to_dict(attr_value)
		
		return attributes


def deserialize_from_dict(data, cls):
	"""
	DESCRIPTION: This function deserializes a dictionary to an object.
	PARAMETERS: data (REQ, dict) - The dictionary to deserialize
				cls (REQ, class) - The class to deserialize the dictionary to
	RETURNS: object - The deserialized object
	"""
	if isinstance(data, (bool, int, long, float, str, unicode)):
		return data
	elif isinstance(data, list):
		return [deserialize_from_dict(item, cls) for item in data]
	elif isinstance(data, dict):
		obj = cls()
		for key, value in data.items():
			setattr(obj, key, deserialize_from_dict(value, cls))
		return obj
	else:
		return data
