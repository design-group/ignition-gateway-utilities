import sys, os, linecache

try:
    """ This is in Ignition, we dont need to import code with file paths added """
    system.util
    import java.lang.Exception
    import General.Logging as Logging
except (NameError, AttributeError, ImportError):
    sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__),os.pardir,os.pardir,os.pardir,os.pardir,os.pardir,'ignition/script-python')))
    import General.Logging.code as Logging

logger = Logging.Logger("General.Errors")

def getException():
	"""
	DESCRIPTION: If you put this in a generic try...except block that continues to raise the error, you can cleanly get a defined error message in the logs, without changing applciation logic.
            	Example Error: 
		            (<module:MES.Workorder>, LINE 270 ""): sequence item 0: expected string, NoneType found
	
	            Example Use:
                    try:
                        # Execute code here	
                    
                    except Exception as e:
                        logger.error(General.Errors.getException())
                        raise(e)
	"""
	exc_type, exc_obj, tb = sys.exc_info()
			
	f = tb.tb_frame
	lineno = tb.tb_lineno
	filename = f.f_code.co_filename
	linecache.checkcache(filename)
	line = linecache.getline(filename, lineno, f.f_globals)
	return '{}({}, LINE {} "{}"): {}'.format(exc_type.__name__, filename, lineno, line.strip(), exc_obj)

class ExceptionWithDetails(Exception):
    """ EXAMPLE:
    try:
        # Execute code here

    except General.Errors.ExceptionWithDetails as e:
		raise(e)
	except Exception as e:
		raise General.Errors.ExceptionWithDetails("A message about my error", logger, e)
    """
    
    def __init__(self, exception_message=None, logger=logger, exception=None, trace=False):
        """
        DESCRIPTION: Exception class that has the ability to add more clear details about where the exception occurs
        PARAMETERS: exception_message (OPT, str) - The message to be displayed in the logs
                    logger (OPT, Logger) - The logger to use for logging
                    exception (OPT, Exception) - The exception to be logged
                    trace (OPT, bool) - True if this should only be logged as a trace, False if it should be logged as an error
        """

        # NOTE: If we passed an ExceptionWithDetails as our exception parameter, than we should just replace this object with it and stop
        if isinstance(exception, ExceptionWithDetails):
            self.__dict__.update(exception.__dict__)
            return 
        
        # NOTE: We can build our list of statements that we want to put in the logs
        message_contents = []

        # NOTE: If this instance is a direct instance of ExceptionWithDetails, than we will get the exception information, and add it to our mesage
        if type(self) == ExceptionWithDetails:
            # NOTE: Lets get our comprehensive details of the exception
            exception_details = getException()
            # NOTE: Add those details into the list of message contents, with a title
            message_contents.append("EXCEPTION: %s" % exception_details)
        
            if exception_message is not None:
                message_contents.append("MESSAGE: %s" % exception_message)
            
            # NOTE: If this is a java.lang.Exception it may have the cause attribute, and we should add it
            if hasattr(exception, "cause"):
                if exception.cause is not None:
                    # NOTE: We could potentially have some nested causes here, so check for a double cause to be present and none first
                    message_contents.append("CAUSE: %s" % (exception.cause.cause or exception.cause))

        # NOTE: If passed a subclass of ExceptionWithDetails, lets just append our message into the list
        else:
            message_contents.append(exception_message)
        
        # NOTE: Join our message contents together into one message to go into the logs
        self.message = ', '.join(message_contents)
        
        # NOTE: This has been disabled, because in this application we likely want to see all specialized exceptions in the logs since we have nowhere else to see them
        # # NOTE: IF this is a direct exception with details, lets throw it in the logs
        if (trace):
            logger.trace(self.message)
        else:
            logger.error(self.message)

        super(ExceptionWithDetails, self).__init__(self.message)