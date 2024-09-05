"""
General.Time
This module contains functions for time data types.
"""
LOGGER = system.util.getLogger("General.Time")

def get_millis_time():
	"""
	DESCRIPTION: Returns the current time in milliseconds
	PARAMETERS: None
	RETURNS: int: The current time in milliseconds
	"""
	return system.date.toMillis(system.date.now())

def round_up_to_hour(datetime):
	"""
	DESCRIPTION: Rounds value up to the nearest hour
	PARAMETERS: datetime (REQ, datetime): The value to be rounded up
	RETURNS: java.util.Date: The rounded up value
	"""
	year = system.date.getYear(datetime)
	day_of_year = system.date.getDayOfYear(datetime)
	hour_plus_one = system.date.getHour24(datetime) + 1
	
	# this ticks the date over if the hour is rounded to midnight
	if hour_plus_one == 0 or hour_plus_one == 24:
		day_of_year += 1
	
	return system.date.parse("%s-%s %s:00:00" % (year, day_of_year, hour_plus_one), "y-D k:m:s")
