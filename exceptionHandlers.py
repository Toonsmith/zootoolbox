import os
import sys
import cgitb
import traceback
from filesystem import findMostRecentDefitionOf


def printMsg( *args ):
	for a in args: print a,


def SHOW_IN_UI():
	from wx import MessageBox, ICON_ERROR
	MessageBox( 'Sorry, it seems an un-expected problem occurred.\nYour error has been reported.  Good Luck!', 'An Unhandled Exception Occurred', ICON_ERROR )


DEFAULT_AUTHOR = 'mel@macaronikazoo.com'

def exceptionHandler( *args ):
	'''
	This is a generic exception handler that can replace the default python exception handler if
	needed (ie: sys.excepthook=exceptionHandler).  It will mail
	'''
	try:
		eType, e, tb = args
	except TypeError:
		eType, e, tb = sys.exc_info()

	printMsg( '### ERROR - Python Unhandled Exception' )
	printMsg( '### ', eType.__name__, e )

	#try to mail a callstack
	try:
		import smtplib
		message = 'Subject: [ERROR] assetEditor\n\n%s' % cgitb.text( args )

		author = findMostRecentDefitionOf( '__author__' ) or DEFAULT_AUTHOR
		svr = smtplib.SMTP( 'exchange2' )
		svr.sendmail(os.environ[ 'USERNAME' ], [author, os.environ[ 'USERNAME' ]], message)
	except Exception, x:
		printMsg( 'ERROR: failed to mail exception dump', x )

	#try to post an error dial
	try:
		SHOW_IN_UI()
	except: pass


def d_handleExceptions(f):
	'''
	if you can't/don't want to setup a generic exception handler, you can decorate a function with
	this to have exceptions handled
	exception hanlding decorator.  basically this decorator will catch any exceptions thrown by the
	decorated function, and spew a useful callstack to the event log - as well as throwing up a dial
	to alert of the issue...
	'''
	def newFunc( *a, **kw ):
		try: f( *a, **kw )
		except:
			exc_info = sys.exc_info()
			exceptionHandler( *exc_info )

	newFunc.__name__ = f.__name__
	newFunc.__doc__ = f.__doc__

	return newFunc


class ExceptionHandledType(type):
	'''
	metaclass that will wrap all callable attributes of a class with the
	d_handleExceptions exception handler decorator above.  this is mainly useful
	for maya/modo, because neither app lets you specify your own global exception
	handler - yet you want to be able to capture this exception data and turn it
	into a meaningful error description that can be sent back to the tool author
	'''
	def __new__( cls, name, bases, attrs ):
		global d_handleExceptions
		newAttrs = {}
		for itemName, item in attrs.iteritems():
			if callable( item ): newAttrs[ itemName ] = d_handleExceptions( item )
			else: newAttrs[ itemName ] = item

		return type.__new__( cls, name, bases, newAttrs )


def generateTraceableStrFactory( prefix, printFunc=None ):
	'''
	returns 2 functions - the first will generate a traceable message string, while
	the second will print the generated message string.  The second is really a
	convenience function, but is called enough to be worth it

	you can also specify your own print function - if no print function is specified
	then the print builtin is used
	'''
	def generateTraceableStr( *args, **kw ):
		frameInfos = inspect.getouterframes( inspect.currentframe() )

		_nFrame = 1
		if '_nFrame' in kw:
			_nFrame = kw[ '_nFrame' ]

		#frameInfos[0] contains the current frame and associated calling data, while frameInfos[1] is the frame that called this one - which is the frame we want to print data about
		callingFrame, callingScript, callingLine, callingName, _a, _b = frameInfos[_nFrame]
		lineStr = 'line %s of the function %s in the script %s' % (callingLine, callingName, callingScript)

		return '%s%s: %s' % (prefix, lineStr, ' '.join( map( str, args ) ))

	def printTraceableStr( *args ):
		msg = generateTraceableStr( _nFrame=2, *args )
		if printFunc is None:
			print( msg )
		else:
			printFunc( msg )

	return generateTraceableStr, printTraceableStr

generateInfoStr, printInfoStr = generateTraceableStrFactory( '*** INFO ***: ' )
generateWarningStr, printWarningStr = generateTraceableStrFactory( '*** WARNING ***: ' )
generateErrorStr, printErrorStr = generateTraceableStrFactory( '*** ERROR ***: ' )


#end
