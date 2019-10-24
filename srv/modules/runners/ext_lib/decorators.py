from functools import wraps
from .exceptions import ModuleException, RunnerException, NoMinionsFound, AbortedByUser
from .utils import humanize_return
from .hash_dir import module_questioneer, pillar_questioneer
import os


def catches(catch=None,
            non_interactive=False,
            called_by_orch=False,
            called_by_runner=False,
            refresh_pillar=True,
            refresh_modules=True):
    """
    This decorator was shamelessly stolen from ceph/ceph's ceph-volume
    and adapted for DeepSea's need.

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
            # TODO: properly assign defaults from the function signature
            non_interactive = kw.get('non_interactive', False)
            called_by_orch = kw.get('called_by_orch', False)
            called_by_runner = kw.get('called_by_runner', False)

            if called_by_runner or called_by_orch:
                # Implicitly setting non_interactive=True
                # when called with those contexts
                non_interactive = True

            if refresh_modules:
                sync_modules(non_interactive)
            if refresh_pillar:
                sync_pillar(non_interactive)

            try:
                results = f(*a, **kw)
            except catch as e:

                # debug
                if os.environ.get('DEEPSEA_DEBUG'):
                    # Useful for unexpected Exceptions that need to be analyzed post mortem
                    # https://docs.python.org/3.7/library/pdb.html#pdb.post_mortem
                    import pdb
                    pdb.post_mortem(e.__traceback__)

                # aborted by user
                if isinstance(e, AbortedByUser):
                    return 'aborted by user.'

                # Known errors
                if isinstance(e, RunnerException) or isinstance(
                        e, ModuleException) or isinstance(e, NoMinionsFound):
                    if called_by_orch:
                        return e.output_for_orchestrator()
                    elif called_by_runner:
                        raise
                    else:
                        print(e.output_for_human())
                    return humanize_return(False)

                # if we don't know about the Exception are should just raise them
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


def sync_modules(non_interactive):
    module_questioneer(non_interactive=non_interactive)

def sync_pillar(non_interactive):
    pillar_questioneer(non_interactive=non_interactive)
