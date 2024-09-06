"""
General.Later

Convenience functions for Ignition development, typically loaded
as "shared.later" in v7.x.
Copyright 2008-2022 Automation Professionals, LLC <sales@automation-pros.com>
Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
  1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.
  3. The name of the author may not be used to endorse or promote products
     derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

from java.lang import Runnable, StackTraceElement, Thread, Throwable
from java.util.concurrent import CompletableFuture
from java.util.function import BiConsumer

import java.lang.Exception
import sys

logger = system.util.getLogger("General."+__name__)

"""
Handle gateway scope where invokeLater doesn't exist.

Generic user code should use General.Later.invokeLater() instead of
system.util.invokeLater() if gateway scope compatibility is needed.
"""
try:
    g = system.util.persistent('General.later')
except:
    g = system.util.getGlobals()

try:
    invokeLater = system.util.invokeLater
except AttributeError:
    try:
        from com.inductiveautomation.ignition.gateway import IgnitionGateway as GwContext
    except:
        from com.inductiveautomation.ignition.gateway import SRContext as GwContext
    _old = g.get('FakeUIThreadExec', None)
    if _old:
        _old.shutdown()
    del _old
    _executor = GwContext.get().createExecutionManager('FakeUIThread', 3)
    g['FakeUIThreadExec'] = _executor
    class _runnable(Runnable):
        def __init__(self, func):
            self.func = func
        def run(self):
            self.func()

    def invokeLater(func, delay=0):
        delay = int(delay)
        if delay>0:
            _executor.executeOnce(_runnable(func), delay)
        else:
            _executor.executeOnce(_runnable(func))

def fullClassName(cls):
    """
    DESCRIPTION: Helper for determining module hierarchy of a class
    PARAMETERS: cls (REQ, class) - The class to get the full name of
    RETURNS: str - The full class name
    """
    if cls.__bases__:
        return fullClassName(cls.__bases__[0])+"."+cls.__name__
    return cls.__name__

class PythonAsJavaException(java.lang.Exception):
    """
    DESCRIPTION: Java wrapper for Jython exceptions to preserve the python stack trace
    PARAMETERS: pyexc (REQ, Exception) - The Python exception to wrap
                tb (OPT, traceback) - The traceback to use
    """
    def __init__(self, pyexc, tb=None):
        """
        DESCRIPTION: Constructor
        PARAMETERS: pyexc (REQ, Exception) - The Python exception to wrap
                    tb (OPT, traceback) - The traceback to use
        RETURNS: None
        """
        super(PythonAsJavaException, self).__init__(repr(pyexc), None, True, True)
        traceElements = []
        if tb is None:
            tb = sys.exc_info()[2]
        while tb:
            code = tb.tb_frame.f_code
            vnames = code.co_varnames
            if vnames and vnames[0] in ('cls', 'self'):
                ref = tb.tb_frame.f_locals[vnames[0]]
                if vnames[0] == 'self':
                    className = fullClassName(ref.__class__)
                else:
                    className = fullClassName(ref)
            else:
                className = '<global>'
            traceElements.append(StackTraceElement(className, code.co_name, code.co_filename, tb.tb_lineno))
            tb = tb.tb_next
        traceElements.reverse()
        self.setStackTrace(traceElements)

def futureExLog(f, retv=None):
    """
    DESCRIPTION: Given a future, wait for it to complete, and log any exception produced at the warning level
        at the warning level.  Return the given value if present, otherwise Return the given value if present, otherwise
        return the future's result.  This function must not be called on the GUI hread -- that will freeze the 
        UI until the future completes.
    PARAMETERS: f (REQ, CompletableFuture) - The future to wait for 
                retv (OPT, any) - The value to return if the future is None
    RETURNS: any - The value of the future
    """
    try:
        if retv is None:
            retv = f.get()
        else:
            f.get()
    except Throwable as t:
        logger.warn("Future Exception:", t)
    return retv

class FutureLogger(BiConsumer):
    """
    DESCRIPTION: A BiConsumer that logs exceptions from a CompletableFuture
    PARAMETERS: otherLogger (OPT, Logger) - A logger to use instead of the default
    """
    def __init__(self, otherLogger=None):
        self.logger = otherLogger if otherLogger else logger
    def accept(self, retv, exc): # pylint: disable=unused-argument
        """
        DESCRIPTION: Accepts the result of a CompletableFuture
        PARAMETERS: retv (REQ, any) - The result of the CompletableFuture
                    exc (REQ, Throwable) - The exception thrown by the CompletableFuture
        RETURNS: None
        """
        if exc:
            self.logger.warn("Future Exception:", exc)

commonLogger = FutureLogger()

def callAsync(func, *args, **kwargs):
    """
    Do *NOT* wait for the future in a GUI thread!
    
    DESCRIPTION: This routine accepts a target function, and a variable argument list, and
        schedules the function call for asynchronous execution.  The function can
        be a bare (no parens) object method, but must not call any gui or
        gui component methods.
    
        The return value of the function completes a future, which is itself returned
        to caller.  If the caller discards the future, the target function's return
        value or exception will be discarded.

    PARAMETERS: func (REQ, function) - The function to call
                args (OPT, list) - The arguments to pass to the function
                kwargs (OPT, dict) - The keyword arguments to pass to the function
    RETURNS: CompletableFuture - The future of the function call
    """
    future = CompletableFuture()
    def callAsyncInvoked():
        """
        DESCRIPTION: Call the function asynchronously
        """
        try:
            future.complete(func(*args, **kwargs))
        except Throwable as t:
            future.completeExceptionally(t)
        except Exception as e:
            future.completeExceptionally(PythonAsJavaException(e))
    system.util.invokeAsynchronous(callAsyncInvoked)
    return future

class JavaCallable(Runnable):
    """
    DESCRIPTION: Java Runnable wrapper for Python Callable with args
    PARAMETERS: Runnable (REQ, Java Runnable) - The Java Runnable to wrap
    """
    __slots__ = ['_f', '_func', '_args', '_kwa']
    def __init__(self, future, func, *args, **kwargs):
        """
        DESCRIPTION: Constructor
        PARAMETERS: future (REQ, CompletableFuture) - The future to complete
                    func (REQ, function) - The function to call
                    args (OPT, list) - The arguments to pass to the function
                    kwargs (OPT, dict) - The keyword arguments to pass to the function
                    RETURNS: None
        """
        self._f = future
        self._func = func
        self._args = args
        self._kwa = kwargs
    def run(self):
        """
        DESCRIPTION: Run the function and complete the future
        """
        try:
            self._f.complete(self._func(*self._args, **self._kwa))
        except Throwable as t:
            self._f.completeExceptionally(t)
        except Exception as e:
            self._f.completeExceptionally(PythonAsJavaException(e))

def callThread(func, threadName, *args, **kwargs):
    """
    Do *NOT* wait for the future in a GUI thread!

    DESCRIPTION: This routine accepts a target function, a thread name, and a variable
        argument list, and schedules the function call for asynchronous execution
        in a java Thread of that name.  The function can
        be a bare (no parens) object method, but must not call any gui or
        gui component methods.
    
        The return value of the function completes a future, which is itself returned
        to the caller (along with the thread itself).  If the caller discards the future,
        the target function's return value or exception will be discarded.

    PARAMETERS: func (REQ, function) - The function to call
                threadName (REQ, str) - The name of the thread to create
                args (OPT, list) - The arguments to pass to the function
                kwargs (OPT, dict) - The keyword arguments to pass to the function
    RETURNS: tuple - The future of the function call and the thread
    """
    future = CompletableFuture()
    runnable = JavaCallable(future, func, *args, **kwargs)
    thread = Thread(runnable, threadName)
    thread.start()
    return (future, thread)

def assignLater(comp, prop, val, ms = 0):
    """
    Do *NOT* wait for the future in a GUI thread!
    
    DESCRIPTION: Procedures executing in the 'invokeAsynchronous' environment are not allowed
        to assign to properties of gui objects.  This routine accepts a target
        object, a property name, and a new value, and schedules the assignment
        in the gui thread.
    
        Successful assignment completes a future with a None value.  The future is
        returned to the caller.  If the caller discards the future, the target
        assignment's success or failure will be discarded.

    PARAMETERS: comp (REQ, object) - The target object to assign the property to
                prop (REQ, str) - The property to assign
                val (REQ, any) - The value to assign
                ms (OPT, int) - The delay in milliseconds before assigning the property
    RETURNS: CompletableFuture - The future of the assignment
    """
    future = CompletableFuture()
    def assignLaterInvoked():
        """
        DESCRIPTION: Assign the value to the property
        """
        try:
            try:
                setattr(comp, prop, val)
            except AttributeError:
                comp.setPropertyValue(prop, val)
            future.complete(None)
        except Throwable as t:
            future.completeExceptionally(t)
        except Exception as e:
            future.completeExceptionally(PythonAsJavaException(e))
    invokeLater(assignLaterInvoked, ms)
    return future

def assignAsyncLater(comp, prop, func, *args, **kwargs):
    """
    Do *NOT* wait for the future in a GUI thread!
    
    DESCRIPTION: Functions executing in the 'invokeAsynchronous' environment are not allowed
        to assign to properties of gui objects.  This routine accepts a target
        object, a property name, a callable function, and its arguments, runs the
        function in the background, then schedules the assignment of the result
        in the gui thread.
    
        Successful assignment completes a future with a None value.  The future is
        returned to the caller.  If the caller discards the future, the target
        assignment's success or failure will be discarded.
    
        Do *NOT* wait for the future in a GUI thread!
    
        An emulation of invokeLater is used in gateway scopes, though somewhat
        pointless, as there are no gui objects in the gateway.  But it works on
        any arbitrary object's properties.
        
    PARAMETERS: comp (REQ, object) - The target object to assign the property to
                prop (REQ, str) - The property to assign
                func (REQ, function) - The function to call
                args (OPT, list) - The arguments to pass to the function
                kwargs (OPT, dict) - The keyword arguments to pass to the function
                RETURNS: CompletableFuture - The future of the function call
    """
    future = CompletableFuture()
    def assignAsyncLaterInvoked():
        """
        DESCRIPTION: Functions executing in the 'invokeAsynchronous' environment are not allowed
        """
        try:
            val = func(*args, **kwargs)
            def assignLaterInvoked():
                """
                DESCRIPTION: Assign the value to the property
                """
                try:
                    try:
                        setattr(comp, prop, val)
                    except AttributeError:
                        comp.setPropertyValue(prop, val)
                except Throwable as t:
                    future.completeExceptionally(t)
                except Exception as e:
                    future.completeExceptionally(PythonAsJavaException(e))
                future.complete(val)
            invokeLater(assignLaterInvoked)
        except Throwable as t:
            future.completeExceptionally(t)
        except Exception as e:
            future.completeExceptionally(PythonAsJavaException(e))
    system.util.invokeAsynchronous(assignAsyncLaterInvoked)
    return future

def callLater(func, *args, **kwargs):
    """
    Do *NOT* wait for the future in a GUI thread!
    
    DESCRIPTION: Procedures executing in the 'invokeAsynchronous' environment are not allowed
        to execute methods of gui objects.  This routine accepts a target
        function, and a variable argument list, and schedules the function call
        in the gui thread.  The function can be a bare (no parens) object method.
    
        If kwargs includes 'ms', that is removed and used in the outer invokeLater
    
        The return value of the function completes a future, which is itself returned
        to caller.  If the caller discards the future, the target function's return
        value or exception will be discarded.
        
    PARAMETERS: func (REQ, function) - The function to call
                args (OPT, list) - The arguments to pass to the function
                kwargs (OPT, dict) - The keyword arguments to pass to the function
    RETURNS: CompletableFuture - The future of the function call
    """
    future = CompletableFuture()
    ms = kwargs.pop('ms', 0)
    def callLaterInvoked():
        """
        DESCRIPTION: Call the function after the delay
        """
        try:
            future.complete(func(*args, **kwargs))
        except Throwable as t:
            future.completeExceptionally(t)
        except Exception as e:
            future.completeExceptionally(PythonAsJavaException(e))
    invokeLater(callLaterInvoked, ms)
    return future

def callAsyncLater(func, *args, **kwargs):
    """
    Do *NOT* wait for the future in a GUI thread!
    
    
    DESCRIPTION: This routine accepts a target function, a variable argument list, and schedules the function call
        for asynchronous execution,but only after also waiting for gui events to complete.  The function can be a bare 
        (no parens) object method, but must not call any gui or gui component methods.
    
    
    The return value of the function completes a future, which is itself returned to caller.  If the caller discards the future,
    the target function's return value or exception will be discarded.
    
    PARAMETERS: func (REQ, function) - The function to call
                args (OPT, list) - The arguments to pass to the function
                kwargs (OPT, dict) - The keyword arguments to pass to the function
    RETURNS: CompletableFuture - The future of the function call
    """
    future = CompletableFuture()
    def callLaterInvoked():
        """
        DESCRIPTION: Call the function after the delay
        """
        def callAsyncInvoked():
            """
            DESCRIPTION: Call the function asynchronously
            """
            try:
                future.complete(func(*args, **kwargs))
            except Throwable as t:
                future.completeExceptionally(t)
            except Exception as e:
                future.completeExceptionally(PythonAsJavaException(e))
        system.util.invokeAsynchronous(callAsyncInvoked)
    invokeLater(callLaterInvoked)
    return future

def callAsyncDelayed(func, delay=1000, *args, **kwargs):
    """
    Do *NOT* wait for the future in a GUI thread!

    DESCRIPTION: This routine accepts a target function, a time, and a variable argument list,
        and schedules the function call for asynchronous execution, but only after also waiting the specified 
        milliseconds after all gui events complete.  The function can be a bare (no parens) object method, but must
        not call any gui or gui component methods.

        The return value of the function completes a future, which is itself returned
        to caller.  If the caller discards the future, the target function's return
        value or exception will be discarded.
    PARAMETERS: func (REQ, function) - The function to call
                delay (OPT, int) - The delay in milliseconds before calling the function
                args (OPT, list) - The arguments to pass to the function
                kwargs (OPT, dict) - The keyword arguments to pass to the function
    RETURNS: CompletableFuture - The future of the function call
    """
    future = CompletableFuture()
    def callLaterInvoked():
        """
        DESCRIPTION: Call the function after the delay
        """
        def callAsyncInvoked():
            """
            DESCRIPTION: Call the function asynchronously
            """
            try:
                future.complete(func(*args, **kwargs))
            except Throwable as t:
                future.completeExceptionally(t)
            except Exception as e:
                future.completeExceptionally(PythonAsJavaException(e))
        system.util.invokeAsynchronous(callAsyncInvoked)
    invokeLater(callLaterInvoked, delay)
    return future

def writeTagLater(tag, val, ms = 0):
    """
    DESCRIPTION: Write a tag synchronously in a background thread
    PARAMETERS: tag (REQ, str) - The tag path to write
                val (REQ, any) - The value to write
                ms (OPT, int) - The delay in milliseconds before writing the tag
                RETURNS: any - The value written
    """
    def writeTagLaterInvoked():
        """
        DESCRIPTION: Write a tag synchronously in a background thread
        """
        system.tag.write(tag, val, True)
    invokeLater(writeTagLaterInvoked, ms)
    return val

def writeTagsLater(taglist, vallist, ms = 0):
    """
    DESCRIPTION: Write a list of tags synchronously in a background thread
    PARAMETERS: taglist (REQ, list) - The list of tag paths to write
                vallist (REQ, list) - The list of values to write
                ms (OPT, int) - The delay in milliseconds before writing the tags
                RETURNS: None
    """
    future = CompletableFuture() #pylint: disable=unused-variable
    def writeTagsLaterInvoked():
        """
        DESCRIPTION: Write a list of tags synchronously in a background thread
        """
        system.tag.writeAll(taglist, vallist)
    invokeLater(writeTagsLaterInvoked, ms)

def writeAsyncAssign(taglist, vallist, comp, prop, val):
    """
    DESCRIPTION: Write a list of tags synchronously in a background thread, then assign a property on the GUI thread
    PARAMETERS: taglist (REQ, list) - The list of tag paths to write
                vallist (REQ, list) - The list of values to write
                comp (REQ, object) - The target object to assign the property to
                prop (REQ, str) - The property to assign
                val (REQ, any) - The value to assign
    RETURNS: None
    """
    def writeAsyncAssignInvoked():
        """
        DESCRIPTION: Write a list of tags synchronously in a background thread, then assign a property on the GUI thread
        """
        for t, v in map(None, taglist, vallist):
            system.tag.writeSynchronous(t, v, 250)
        app.util.assignLater(comp, prop, val)
    system.util.invokeAsynchronous(writeAsyncAssignInvoked)
