import pytest
from mock import patch, create_autospec, mock

def pass_through(*args):
    return args[0]

@pytest.fixture(scope='class')
def helper_specs(module=None, ret_val=(0, 'stdout', 'stderr'), side_effect=pass_through):
    """
    A module wide fixture that adds a dict that mirrors salt's __salt__
    injection.

    Explanation:
    We have helper functions in our srv/salt/_modules/helper.py module
    which should be accessed via the __salt__ global that salt injects
    during runtime.

    __salt__ is a dict and looks like so:
    __salt__ = {'module.function': <uninstantiated-function>, ...}

    The test however does not inject this dunder and needs to be populated.
    You also need to be able to set the return_value of your module.function
    depending on the context of the test.

    **helper.run**

    Simple Example:

    In the code:
    __salt__['helper.run']('a dymanically constructed command')

    In the test:
    test_module = helper_specs(module=module_to_test)
    test_module.__salt__['helper.run'].assert_called_with('a dynamically constructed command')

    A More complex Example:

    In the code:
    def your_method():
        rc, stdout, stderr = __salt__['helper.run']('a dymanically constructed command')
        if stdout == 'a':
            do_a
        elif stdout == 'b':
            do_b
        else:
        ....

    In the test:
    You now need to test for at least 3 different cases.
    A) stdout == 'a'
    B) stdout == 'b'
    C) stdout == not 'a' and not 'b'

    That requires you to mock the output of __salt__['helper.run'](cmd).
    With this fixture you get the mocked version of the module back.

    test_module = helper_specs(module=module_to_test)
    test_module.__salt__['helper.run'].return_value = 'a'
    test_module.your_method()
    do_a.assert_called_once()
    assert not do_b.called

    ... same dance for 'b' and 'x'

    **helper.convert_out**

    This helper exists because of the python2-3 conversion and the
    associated changes to type(bytes, strings and unicode).
    Read more on that here: http://python3porting.com/problems.html

    tl;dr: We need to check for bytes/string and decode when needed.

    In the test however you don't really care what's being stuffed
    in that helper. There is one caveat though. In the code we often
    overwrite a local runtime variable.

    Example:
    ```
    for line in stdout:
        line = __salt__['helper.convert_out'](line)
        print_or_handle(line)
        #^ only accepts strings and needs to be converted.
    ```

    Without proper mocking 'line' would always be 'None' in the tests.
    So what you want to do is basically mock the 'helper.convert_out'
    function to 'pass through' every piece of data that it receives.
    (Magic)Mocks have a feature called 'side_effect' that allows you
    to pass a function that generates the return_values dynamically.
    I'm abusing that feature to always return the first argument passed to it.
    (convert_out only ever takes _one_ arg, hence the arg[0])

    module: a module like 'osd' or 'cephdisks'
    ret_val: return value of 'helper.run', tuple(rc, stdout, stderr)
    side_effects: method of returning data for 'helper.convert_out'

    returns <specs <module> >
    """
    def specs(module=module, ret_val=ret_val):
        convert_out_mock = create_autospec(lambda x: x, side_effect=pass_through)
        run_mock = create_autospec(lambda x: x, return_value=ret_val)
        module.__salt__ = {'helper.run': run_mock,
                           'helper.convert_out': convert_out_mock}
        return module
    return specs
