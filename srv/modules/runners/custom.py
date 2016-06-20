
from layouts import *

class CustomLayout(LayoutsByHostname):
    """
    Define custom class by overriding specific methods of an existing
    layout class
    """

    def monitors(self, name, servers, number):
        """
        Alter hardcoded role based names to your liking.
        """
        monitors = filter(lambda m: 'myz' in m, servers)
        if len(monitors) < number:
            monitors = servers[0:number]
        return { 'name': name, 'monitors': monitors }


def custom_layout():
    """
    Hook back to main file for salt-runner
    """
    return CustomLayout
