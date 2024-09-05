"""
General.Timed
This module provides decorators for timing functions and collecting timing data.
"""

LOGGER = system.util.getLogger("General.Timed")

GLOBALS = system.util.globals

def execute_timed(func):
	"""
	Decorator to time the execution of a function.
	"""
	def wrapper(*args, **kwargs):
		"""
		DESCRIPTION: Wrapper function to time the execution of the decorated function.
		"""
		start = system.date.now()
		GLOBALS['START_TIMES'].append(start)
		result = func(*args, **kwargs)
		end = system.date.now()
		start = GLOBALS['START_TIMES'].pop()
		execution_time = system.date.millisBetween(start, end)
		
		if func.__name__ not in GLOBALS['TIMING_REPORT']:
			GLOBALS['TIMING_REPORT'][func.__name__] = {
				'total_duration': execution_time,
				'call_count': 1
			}
		else:
			GLOBALS['TIMING_REPORT'][func.__name__]['total_duration'] += execution_time
			GLOBALS['TIMING_REPORT'][func.__name__]['call_count'] += 1
		
		if func.__name__ not in GLOBALS['ELAPSED_DATA']:
			GLOBALS['ELAPSED_DATA'][func.__name__] = execution_time
		else:
			GLOBALS['ELAPSED_DATA'][func.__name__] += execution_time
		
		return result
	return wrapper

def collect_timing_report(func):
	"""
	Decorator to collect timing data and print a report at the end of the script.
	"""
	def wrapper(*args, **kwargs):
		"""
		DESCRIPTION: Wrapper function to collect timing data and print a report at the end of the script.
		"""
		GLOBALS['TIMING_REPORT'] = {}
		GLOBALS['ELAPSED_DATA'] = {}
		GLOBALS['START_TIMES'] = []
		start = system.date.now()
		GLOBALS['START_TIMES'].append(start)
		result = func(*args, **kwargs)
		end = system.date.now()
		start = GLOBALS['START_TIMES'].pop()

		total_duration = system.date.millisBetween(start, end)

		message = "Timing Report:\n"
		message += "Total duration: %s ms\n\n" % total_duration

		message += "Top 5 Longest-Running Functions:\n"
		sorted_timings = sorted(GLOBALS['TIMING_REPORT'].items(), key=lambda x: x[1]['total_duration'], reverse=True)
		for func_name, data in sorted_timings[:5]:
			message += "Function %s: %s ms\n" % (func_name, data['total_duration'])

		message += "\nTop 5 Most Called Functions:\n"
		sorted_calls = sorted(GLOBALS['TIMING_REPORT'].items(), key=lambda x: x[1]['call_count'], reverse=True)
		for func_name, data in sorted_calls[:5]:
			message += "Function %s: %s calls\n" % (func_name, data['call_count'])

		message += "\nFunction Breakdown (Elapsed Time):\n"
		for func_name, elapsed_time in GLOBALS['ELAPSED_DATA'].items():
			message += "Function %s: %s ms\n" % (func_name, elapsed_time)

		LOGGER.info(message)

		return result
	return wrapper
