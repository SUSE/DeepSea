from functools import wraps
from .exceptions import ModuleException, RunnerException
from .utils import humanize_return
import os


def catches(catch=None, called_by_orch=False, called_by_runner=False):
    """
    Very simple decorator that tries any of the exception(s) passed in as
    a single exception class or tuple (containing multiple ones) returning the
    exception message and optionally handling the problem if it rises with the
    handler if it is provided.
    So instead of douing something like this::
        def bar():
            try:
                some_call()
                print "Success!"
            except TypeError, exc:
                print "Error while handling some call: %s" % exc
                sys.exit(1)
    You would need to decorate it like this to have the same effect::
        @catches(TypeError)
        def bar():
            some_call()
            print "Success!"
    If multiple exceptions need to be caught they need to be provided as a
    tuple::
        @catches((TypeError, AttributeError))
        def bar():
            some_call()
            print "Success!"
    """
    catch = catch or Exception

    def decorate(f):
        @wraps(f)
        def newfunc(*a, **kw):
            try:
                results = f(*a, **kw)
            except catch as e:

                # TODO: eval
                if os.environ.get('IS_THIS_SOMETHING_FOR_US?'):
                    raise

                if isinstance(e, RunnerException) or isinstance(
                        e, ModuleException):
                    if kw.get('called_by_orch', called_by_orch):
                        return e.output_for_orchestrator()
                    elif kw.get('called_by_runner', called_by_runner):
                        raise
                    else:
                        print(e.output_for_human())
                    return humanize_return(False)

                # if we don't know what the Exceptions are
                # we should just raise them
                raise

            else:
                if kw.get('called_by_runner', called_by_runner):
                    # This needs an aggregated result from the TODO above
                    return results
                if kw.get('called_by_orch', called_by_orch):
                    # what does the orchestrator expect. We can pass whatever we need here
                    return results

                return humanize_return(all(results))

            finally:
                pass

        return newfunc

    return decorate
