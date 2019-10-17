from .validator import evaluate_module_return
from .exceptions import ModuleException
from .utils import LocalClient

def exec_module(module='', function='', target='', arguments=[], **kwargs):
    """"""
    raise_on_failure = kwargs.get('raise_on_failure', True)
    tgt_type = kwargs.get('tgt_type', 'pillar')

    assert module
    assert function
    assert target


    """ This is just a test for my local environment """
    ret = LocalClient().cmd(
        target, f'{module}.{function}', arguments, tgt_type=tgt_type)

    if not evaluate_module_return(ret):
        # evaluate_module_return_new writes a detailed message to the screen
        if raise_on_failure:
            raise ModuleException(False, ret)
        return (False, ret)
    return (True, ret)
