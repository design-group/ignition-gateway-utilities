"""
This module provides a wrapper for toast notifications in Ignition using react-toastify and Embr-Periscope.
It simplifies the process of displaying toast notifications with various configurations and types.
"""
from collections import OrderedDict
from java.util import Exception as JavaException

LOGGER = system.util.getLogger("General.Toast")


class ToastWrapper:
	"""
	A Python wrapper for react-toastify to simplify toast notifications in Ignition.
	"""
	# Default configuration for toasts
	DEFAULT_CONFIG = {
		"position": "top-right",
		"autoClose": 5000,  # Default auto-close time in milliseconds
		"hideProgressBar": False,
		"closeOnClick": True,
		"pauseOnHover": True,
		"draggable": True,
		"progress": None,
		"theme": "colored",
		"closeButton": True
	}

	# Valid options for certain fields to enforce consistency
	VALID_POSITIONS = ["top-right", "top-center", "top-left", "bottom-right", "bottom-center", "bottom-left"]
	VALID_THEMES = ["light", "dark", "colored"]

	# Default configurations for specific toast types
	TOAST_TYPE_CONFIGS = {
		"action": {
			"type": "info",
			"className": "psc-toast-action"
		},
		"success": {
			"type": "success",
			"className": "psc-toast-success"
		},
		"warning": {
			"type": "warning",
			"className": "psc-toast-warn"
		},
		"error": {
			"type": "error",
			"className": "psc-toast-error"
		},
		"default": {}
	}

	def __init__(self):
		"""Initialize the ToastWrapper with default settings."""
		self.config = self.DEFAULT_CONFIG.copy()

	def toast(self, message, config_obj):
		"""
		Display a toast notification with the given message and configuration.

		Args:
			message (str): The message to display in the toast.
			config_obj: Optional toast configuration (e.g., position, autoClose, theme).

		Returns:
		   ម: None: Executes the toast command asynchronously via JavaScript.
		"""
		# If we are not in a Perspective scope, do nothing, as toasts are only supported in Perspective.
		if not General.Utilities.is_perspective_scope():
			return

		# Merge default config with user-provided config_obj
		toast_config = self.config.copy()
		toast_config.update(config_obj)

		# Validate specific fields
		self._validate_config(toast_config)

		# Build the JavaScript toast command
		js_config = self._build_js_config(toast_config)
		# Escape message to prevent JS injection
		escaped_message = message.replace("'", "\\'")
		toast_type = toast_config.get("type")

		if toast_type and toast_type != "default":
			toast_command = "periscope.toast.%s('%s', %s);" % (toast_type, escaped_message, js_config)
		else:
			toast_command = "periscope.toast('%s', %s);" % (escaped_message, js_config)

		# Execute the JavaScript asynchronously with error handling
		try:
			system.perspective.runJavaScriptAsync("() => %s" % toast_command)
		except JavaException as e:
			LOGGER.error("Failed to execute toast: %s" % str(e))

	def _validate_config(self, config):
		"""
		Validate the toast configuration to ensure valid values.

		Args:
			config (dict): The toast configuration to validate.

		Raises:
			ValueError: If an invalid configuration value is provided.
		"""
		if config.get("position") not in self.VALID_POSITIONS:
			raise ValueError("Invalid position. Must be one of: %s" % ", ".join(self.VALID_POSITIONS))
		if config.get("theme") not in self.VALID_THEMES:
			raise ValueError("Invalid theme. Must be one of: %s" % ", ".join(self.VALID_THEMES))
		if "transition" in [key.lower() for key in config.keys()]:
			raise NotImplementedError("Transition is not supported in this version of toasts.")

	def _build_js_config(self, config):
		"""
		Build the JavaScript configuration string from the Python config dict.

		Args:
			config (dict): The toast configuration.

		Returns:
			str: A JavaScript-compatible configuration string.
		"""
		js_config = OrderedDict()
		for key, value in config.items():
			if value is None:
				js_config[key] = "undefined"
			elif isinstance(value, bool):
				js_config[key] = str(value).lower()
			elif isinstance(value, (int, float)):
				js_config[key] = str(value)
			else:
				js_config[key] = '"%s"' % value

		# Join the key-value pairs into a JavaScript object string
		return "{" + ",".join("%s: %s" % (k, v) for k, v in js_config.items()) + "}"

	def set_default_config(self, config_obj):
		"""
		Update the default configuration for all future toasts.

		Args:
			config_obj: Configuration options to update (e.g., theme, position).
		"""
		self.config.update(config_obj)
		self._validate_config(self.config)


def show_action_toast(message, config_obj=None):
	"""
	Display an info toast with the given message.

	Args:
		message (str): The message to display.
		config_obj: Optional configuration overrides.
	"""
	toaster = ToastWrapper()
	config = toaster.TOAST_TYPE_CONFIGS["action"].copy()
	if config_obj:
		config.update(config_obj)
	toaster.toast(message, config)


def show_success_toast(message, config_obj=None):
	"""
	Display a success toast with the given message.

	Args:
		message (str): The message to display.
		config_obj: Optional configuration overrides.
	"""
	toaster = ToastWrapper()
	config = toaster.TOAST_TYPE_CONFIGS["success"].copy()
	if config_obj:
		config.update(config_obj)
	toaster.toast(message, config)


def show_warning_toast(message, config_obj=None):
	"""
	Display a warning toast with the given message.

	Args:
		message (str): The message to display.
		config_obj: Optional configuration overrides.
	"""
	toaster = ToastWrapper()
	config = toaster.TOAST_TYPE_CONFIGS["warning"].copy()
	if config_obj:
		config.update(config_obj)
	toaster.toast(message, config)


def show_error_toast(message, config_obj=None):
	"""
	Display an error toast with the given message.

	Args:
		message (str): The message to display.
		config_obj: Optional configuration overrides.
	"""
	toaster = ToastWrapper()
	config = toaster.TOAST_TYPE_CONFIGS["error"].copy()
	if config_obj:
		config.update(config_obj)
	toaster.toast(message, config)


def show_toast_by_type(toast_type, message, config_obj=None):
	"""
	Display a default toast with the given message.

	Args:
		message (str): The message to display.
		config_obj: Optional configuration overrides.
	"""
	if toast_type.lower() not in ToastWrapper.TOAST_TYPE_CONFIGS:
		raise ValueError("Invalid toast type. Must be one of: %s" % ", ".join(ToastWrapper.TOAST_TYPE_CONFIGS.keys()))
	toaster = ToastWrapper()
	config = toaster.TOAST_TYPE_CONFIGS[toast_type.lower()].copy()
	if config_obj:
		config.update(config_obj)
	toaster.toast(message, config)


def show_toast(message, config_obj=None):
	"""
	Display a generic toast with the given message and configuration.

	Args:
		message (str): The message to display.
		config_obj: Optional toast configuration (e.g., position, autoClose, theme).
	"""
	toaster = ToastWrapper()
	config = toaster.TOAST_TYPE_CONFIGS["default"].copy()
	if config_obj:
		config.update(config_obj)
	toaster.toast(message, config)
