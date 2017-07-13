import salt.client
import salt.utils.error

class UpgradeValidation(object):
    """
    Due to the current situation you have to upgrade
    all monitos before ceph allows you to start any OSD
    Our current implementation of maintenance upgrades
    triggers this behavior if you happen to have
    Monitors and Storage roles assigned on the same node
    (And more then one monitor)
    To avoid this, before actually providing a proper solution,
    we stop users to execute the upgade in the first place.
    """

    def __init__(self, cluster='ceph'):
        local = salt.client.LocalClient()
        search = "I@cluster:{}".format(cluster)

        self.pillar_data = local.cmd(search , 'pillar.items', [], expr_form="compound")
        self.grains_data = local.cmd(search , 'grains.items', [], expr_form="compound")

    def colocated_services(self):
        pillar_data = self.pillar_data
        for host in pillar_data.keys():
            if 'roles' in pillar_data[host]:
                if 'storage' in pillar_data[host]['roles']\
                    and 'mon' in pillar_data[host]['roles']:
                    msg = """
                         ************** PLEASE READ ***************
                         We currently do not support upgrading when
                         you have a monitor and a storage role
                         assigned on the same node.
                         ******************************************"""
                    return False, msg
        return True, ""

def check():
      uvo = UpgradeValidation()
      ret, msg = uvo.colocated_services()
      print msg
      return ret
