
"""
The layouts are the reasonable proposals or suggestions for a Ceph cluster
with the available hardware.  With enough servers, other combinations are
definitely possible and these lists are not exhaustive.

Each proposal suggests the assignment of servers to a role with a fairly simple naming scheme of the role.  The roles are 

    mon - Ceph monitor nodes
    mds - metadata server to support CephFS
    rgw - Rados Gateway 
    igw - iSCSI gateway 

Storage nodes have unpartitioned free disks.
"""

import pprint


class DefaultLayouts(object):
    """
    Create proposals as though all free servers are identical hardware with
    insignificant names (i.e. cattle)

    Note that some configurations allow for a quantity of monitors greater
    than the number of free servers.  This is intentional for planned growth.
    """

    def __init__(self, storage, free):
        """
        Track storage and free servers

            storage - list
            free - list
        """
        self.storage = storage
        self.free = free

    def zero_free(self):
        """
        All servers are storage
        """
        return [ 
            { 'mon': self.storage[0:3],
              'name': '3monitor' },
            { 'mon': self.storage[0:3],
              'name': '3monitor&2mds',
              'mds': self.storage[0:2] }
        ]

    def one_free(self):
        """
        One server is free, possibly a proof of concept
        """
        return [ 
            { 'mon': self.storage[0:3],
              'name': '3monitor+rgw',
              'rgw': self.free },
            { 'mon': self.storage[0:3],
              'name': '3monitor+igw',
              'igw': self.free }
        ]
                       

    def two_free(self):
        """
        Two free servers to serve as redundant nodes
        """
        return [ 
            { 'mon': self.storage[0:3],
              'name': '3monitor+2mds',
              'mds': self.free },
            { 'mon': self.storage[0:3],
              'name': '3monitor+2rgw',
              'rgw': self.free },
            { 'mon': self.storage[0:3],
              'name': '3monitor+2igw',
              'igw': self.free }
        ]

    def three_free(self):
        """
        Three free servers create several possibilites from independent
        monitors to three redundant gateways
        """
        return [ 
            { 'mon': self.free, 
              'name': '3monitor' },
            { 'mon': self.free, 
              'name': '4monitor' },
            { 'mon': self.free, 
              'name': '5monitor' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '3monitor&2mds' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '4monitor&2mds' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '5monitor&2mds' },
            { 'mon': self.storage[0:3],
              'rgw': self.free,
              'name': '3monitor+3rgw' },
            { 'mon': self.storage[0:4],
              'rgw': self.free,
              'name': '4monitor+3rgw' },
            { 'mon': self.storage[0:5],
              'rgw': self.free,
              'name': '5monitor+3rgw' },
            { 'mon': self.storage[0:3],
              'igw': self.free,
              'name': '3monitor+3igw' },
            { 'mon': self.storage[0:4],
              'igw': self.free,
              'name': '4monitor+3igw' },
            { 'mon': self.storage[0:5],
              'igw': self.free,
              'name': '5monitor+3igw' },
        ]

    def four_free(self):
        """
        Four free servers allows independent monitors or two sets of
        redundant gateways
        """
        return [ 
            { 'mon': self.free[0:3], 
              'name': '3monitor' },
            { 'mon': self.free, 
              'name': '4monitor' },
            { 'mon': self.free, 
              'name': '5monitor' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'name': '3monitor&2mds' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '4monitor&2mds' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '5monitor&2mds' },
            { 'mon': self.storage[0:3],
              'rgw': self.free[0:2],
              'igw': self.free[2:4],
              'name': '3monitor+2rgw+2igw' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '4monitor&2mds' },
            { 'mon': self.storage[0:4],
              'rgw': self.free[0:2],
              'igw': self.free[2:4],
              'name': '4monitor+2rgw+2igw' },
            { 'mon': self.storage[0:5],
              'rgw': self.free[0:2],
              'igw': self.free[2:4],
              'name': '5monitor+2rgw+2igw' }
        ]

    def five_free(self):
        """
        Five free servers allows independent monitors and a redundant
        gateway or shared monitors with redundant gateways
        """
        return [ 
            { 'mon': self.free[0:3], 
              'mds': self.free[3:5],
              'name': '3monitor+2mds' },
            { 'mon': self.free, 
              'name': '4monitor' },
            { 'mon': self.free, 
              'name': '5monitor' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'rgw': self.free[2:4],
              'name': '3monitor&2mds+2rgw' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'igw': self.free[2:4],
              'name': '3monitor&2mds+2igw' },
            { 'mon': self.free[0:4],
              'mds': self.free[0:2],
              'name': '4monitor&2mds' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '5monitor&2mds' },
            { 'mon': self.storage[0:3],
              'rgw': self.free[0:3],
              'igw': self.free[3:5],
              'name': '3monitor+3rgw+2igw' },
            { 'mon': self.storage[0:3],
              'rgw': self.free[0:2],
              'igw': self.free[2:5],
              'name': '3monitor+2rgw+3igw' },
            { 'mon': self.free,
              'mds': self.free[0:2],
              'name': '5monitor&2mds' }
        ]

    def six_free(self):
        """
        Six free servers allows independent monitors and three way 
        redundant gateways
        """
        return [ 
            { 'mon': self.free[0:4], 
              'mds': self.free[4:6],
              'name': '4monitor+2mds' },
            { 'mon': self.free[0:4], 
              'mds': self.free[0:2],
              'rgw': self.free[4:6],
              'name': '4monitor&2mds+2rgw' },
            { 'mon': self.free[0:4], 
              'rgw': self.free[4:6],
              'name': '4monitor+2rgw' },
            { 'mon': self.free[0:4], 
              'igw': self.free[4:6],
              'name': '4monitor+2igw' },
            { 'mon': self.free[0:4], 
              'mds': self.free[0:2],
              'igw': self.free[4:6],
              'name': '4monitor&2mds+2igw' },
            { 'mon': self.free, 
              'name': '5monitor' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'rgw': self.free[3:6],
              'name': '3monitor&2mds+3rgw' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'igw': self.free[3:6],
              'name': '3monitor&2mds+3igw' },
            { 'mon': self.free[0:5],
              'mds': self.free[0:2],
              'name': '5monitor&2mds' },
            { 'mon': self.storage[0:3],
              'rgw': self.free[3:6],
              'name': '3monitor+3rgw' },
            { 'mon': self.storage[0:3],
              'igw': self.free[3:6],
              'name': '3monitor+3igw' }
        ]

    def seven_free(self):
        """
        Seven free servers presents many permutations from five monitors
        and a redundant gateway to three monitors with two redundant
        gateways.
        """
        return [ 
            { 'mon': self.free[0:5], 
              'mds': self.free[5:7],
              'name': '5monitor+2mds' },
            { 'mon': self.free[0:4], 
              'mds': self.free[0:2],
              'rgw': self.free[4:7],
              'name': '4monitor&2mds+3rgw' },
            { 'mon': self.free[0:4], 
              'rgw': self.free[4:7],
              'name': '4monitor+3rgw' },
            { 'mon': self.free[0:4], 
              'mds': self.free[0:2],
              'igw': self.free[4:7],
              'name': '4monitor&2mds+3igw' },
            { 'mon': self.free[0:4], 
              'igw': self.free[4:7],
              'name': '4monitor+3igw' },
            { 'mon': self.free[0:5],
              'mds': self.free[0:2],
              'rgw': self.free[5:7],
              'name': '5monitor&2mds+2rgw' },
            { 'mon': self.free[0:5],
              'mds': self.free[0:2],
              'igw': self.free[5:7],
              'name': '5monitor&2mds+2igw' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'rgw': self.free[3:7],
              'name': '3monitor&2mds+4rgw' },
            { 'mon': self.free[0:3],
              'rgw': self.free[3:7],
              'name': '3monitor+4rgw' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'igw': self.free[3:7],
              'name': '3monitor&2mds+4igw' },
            { 'mon': self.free[0:3],
              'igw': self.free[3:7],
              'name': '3monitor+4igw' },
            { 'mon': self.free[0:3],
              'mds': self.free[0:2],
              'rgw': self.free[3:5],
              'igw': self.free[5:7],
              'name': '3monitor&2mds+2rgw+2igw' },
            { 'mon': self.free[0:3],
              'rgw': self.free[3:5],
              'igw': self.free[5:7],
              'name': '3monitor+2rgw+2igw' },
        ]


class LayoutsByHostname(object):
    """
    Create proposals but server names represent roles.  Any hostname
    containing the string 'mon' is designated as a monitor.  The remaining
    servers are allocated to other roles.

    In the cases of many available servers and multiple gateway roles, any
    hostname containing the gateway role (e.g. 'igw' or 'rgw') is designated
    for that role.

    Note that some configurations allow for a quantity of monitors greater
    than the number of free servers.  This is intentional for planned growth.
    """

    def __init__(self, storage, free):
        """
        Track storage and free servers

            storage - list
            free - list
        """
        self.storage = storage
        self.free = free

    def monitors(self, name, servers, number):
        """
        Assign all hostnames containing 'mon' to monitors.  If the matches
        are insufficient for the requested number, then default to the
        first servers in the list.
        """
        monitors = filter(lambda m: 'mon' in m, servers)  
        if len(monitors) < number:
            monitors = servers[0:number] 
        return { 'name': name, 'mon': monitors }    

    def monitors_with_mds(self, name, servers, number):
        """
        Use the first two monitor servers as mds
        """
        result = self.monitors(name, servers, number)
        mds = result['mon'][0:2]
        result['mds'] = mds
        return result

    def zero_free(self):
        """
        No free servers, suggest shared monitors on storage
        """
        return [ 
            self.monitors('3monitor', self.storage, 3),
            self.monitors_with_mds('3monitor&2mds', self.storage, 3)
        ]

    def monitors_and(self, name, servers, number, role, servers2, count=1):
        """
        Add a role to the monitors
        """
        result = self.monitors(name, servers, number)
        result[role] = servers2[0:count]
        return result


    def one_free(self):
        """
        One server is free, possibly a proof of concept
        """
        return [ 
            self.monitors_and('3monitor+rgw', self.storage, 3, 'rgw', self.free),
            self.monitors_and('3monitor+igw', self.storage, 3, 'igw', self.free),
        ]

    def two_free(self):
        """
        Two free servers to serve as redundant nodes
        """
        return [ 
            self.monitors_and('3monitor+2mds', self.storage, 3, 'mds', self.free, 2),
            self.monitors_and('3monitor+2rgw', self.storage, 3, 'rgw', self.free, 2),
            self.monitors_and('3monitor+2igw', self.storage, 3, 'igw', self.free, 2),
        ]

    def three_free(self):
        """
        Three free servers create several possibilites from independent
        monitors to three redundant gateways
        """
        return [ 
            self.monitors('3monitor', self.free, 3),
            self.monitors('4monitor', self.free, 3),
            self.monitors('5monitor', self.free, 3),
            self.monitors_with_mds('3monitor&2mds', self.free, 3),
            self.monitors_with_mds('4monitor&2mds', self.free, 3),
            self.monitors_with_mds('5monitor&2mds', self.free, 3),
            self.monitors_and('3monitor+3rgw', self.storage, 3, 'rgw', self.free, 3),
            self.monitors_and('4monitor+3rgw', self.storage, 4, 'rgw', self.free, 3),
            self.monitors_and('5monitor+3rgw', self.storage, 5, 'rgw', self.free, 3),
            self.monitors_and('3monitor+3igw', self.storage, 3, 'igw', self.free, 3),
            self.monitors_and('4monitor+3igw', self.storage, 4, 'igw', self.free, 3),
            self.monitors_and('5monitor+3igw', self.storage, 5, 'igw', self.free, 3),
        ]

    def _role_assign(self, role1, role2, servers, count1, count2):
        """
        Assign servers by role.  If server names are inconsistent, attempt
        to assign at least one role and use the remaining for the other. If
        nothing matches or matches are insufficient, default to splitting
        the list.
        """
        result = {}
        result[role1] = filter(lambda x: role1 in x, servers)
        result[role2] = filter(lambda x: role2 in x, servers)

        if len(result[role1]) != count1:
            result[role1] = None
        if len(result[role2]) != count2:
            result[role2] = None

        if result[role1]:
            if result[role2]:
                pass
            else:
                result[role2] = list(set(servers) - set(result[role1]))
        else:
            if result[role2]:
                result[role1] = list(set(servers) - set(result[role2]))
            else:
                result[role1] = servers[0:count1]
                result[role2] = servers[count1:count1 + count2]
        return result


    def monitors_2and(self, name, servers, number, role1, role2, servers2, count1, count2):
        """
        Create a proposal of monitors on storage and two additional separate 
        roles
        """
        result = self.monitors(name, servers, number)
        result.update(self._role_assign(role1, role2, servers2, count1, count2))
        return result

    def four_free(self):
        """
        Four free servers allows independent monitors or two sets of
        redundant gateways
        """
        return [ 
            self.monitors('3monitor', self.free, 3),
            self.monitors('4monitor', self.free, 4),
            self.monitors('5monitor', self.free, 4),
            self.monitors_with_mds('3monitor&2mds', self.free, 3),
            self.monitors_with_mds('4monitor&2mds', self.free, 4),
            self.monitors_with_mds('5monitor&2mds', self.free, 4),
            self.monitors_2and('3monitor+2rgw+2igw', self.storage, 3, 'rgw', 'igw', self.free, 2, 2),
            self.monitors_2and('4monitor+2rgw+2igw', self.storage, 4, 'rgw', 'igw', self.free, 2, 2),
            self.monitors_2and('5monitor+2rgw+2igw', self.storage, 4, 'rgw', 'igw', self.free, 2, 2),
        ]

    def monitors_with_mds_and(self, name, servers, number, role, count):
        """
        Create a proposal of monitors with two mds and designate the remaining
        servers for a role
        """
        result = self.monitors(name, servers, number)
        remaining = list(set(servers) - set(result['mon']))
        mds = result['mon'][0:2]
        result['mds'] = mds
        result[role] = remaining[0:count]
        return result

    def monitors_xor(self, name, servers, number, role, count=1):
        """
        Create a proposal of monitors and designate the remaining servers for a
        role
        """
        result = self.monitors(name, servers, number)
        remaining = list(set(servers) - set(result['mon']))
        result[role] = remaining[0:count]
        return result

    def five_free(self):
        """
        Five free servers allows independent monitors and a redundant
        gateway or shared monitors with redundant gateways
        """
        return [ 
            self.monitors_xor('3monitor+2mds', self.free, 3, 'mds', 2),
            self.monitors('4monitor', self.free, 4),
            self.monitors('5monitor', self.free, 4),
            self.monitors_with_mds('5monitor&2mds', self.free, 5),
            self.monitors_with_mds_and('3monitor&2mds+2rgw', self.free, 3, 'rgw',  2),
            self.monitors_with_mds_and('3monitor&2mds+2igw', self.free, 3, 'igw',  2),
            self.monitors_with_mds('4monitor&2mds', self.free, 4),
            self.monitors_with_mds('5monitor&2mds', self.free, 5),
            self.monitors_2and('3monitor+3rgw+2igw', self.storage, 3, 'rgw', 'igw', self.free, 3, 2),
            self.monitors_2and('3monitor+2rgw+3igw', self.storage, 3, 'rgw', 'igw', self.free, 2, 3),
        ]

    def six_free(self):
        """
        Six free servers allows independent monitors and three way 
        redundant gateways
        """
        return [ 
            self.monitors_xor('4monitor+2mds', self.free, 4, 'mds', 2),
            self.monitors_xor('4monitor+2rgw', self.free, 4, 'rgw', 2),
            self.monitors_xor('4monitor+2igw', self.free, 4, 'igw', 2),
            self.monitors_with_mds_and('4monitor&2mds+2rgw', self.free, 4, 'rgw',  2),
            self.monitors_with_mds_and('4monitor&2mds+2igw', self.free, 4, 'igw',  2),
            self.monitors('5monitor', self.free, 4),
            self.monitors_with_mds_and('3monitor&2mds+3rgw', self.free, 3, 'rgw',  3),
            self.monitors_with_mds_and('3monitor&2mds+3igw', self.free, 3, 'igw',  3),
            self.monitors_with_mds('5monitor&2mds', self.free, 5),
            self.monitors_xor('3monitor+3rgw', self.free, 3, 'rgw', 3),
            self.monitors_xor('3monitor+3igw', self.free, 3, 'igw', 3),
        ]


    def monitors_2xor(self, name, servers, number, role1, role2, count1, count2):
        """
        Create a proposal of monitors and designate the remaining servers for 
        two roles
        """
        result = self.monitors(name, servers, number)
        remaining = list(set(servers) - set(result['mon']))
        result.update(self._role_assign(role1, role2, remaining, count1, count2))
        return result

    def monitors_with_mds_2xor(self, name, servers, number, role1, role2, count1, count2):
        """
        Create a proposal of monitors with two mds and designate the remaining 
        servers for two roles
        """
        result = self.monitors_2xor(name, servers, number, role1, role2, count1, count2)
        result['mds'] = result['mon'][0:2]
        return result

    def seven_free(self):
        """
        Seven free servers presents many permutations from five monitors
        and a redundant gateway to three monitors with two redundant
        gateways.
        """
        return [ 
            self.monitors_xor('5monitor+2mds', self.free, 5, 'mds', 2),
            self.monitors_with_mds_and('4monitor&2mds+3rgw', self.free, 4, 'rgw',  3),
            self.monitors_with_mds_and('4monitor&2mds+3igw', self.free, 4, 'igw',  3),
            self.monitors_xor('4monitor+3rgw', self.free, 4, 'rgw', 3),
            self.monitors_xor('4monitor+3igw', self.free, 4, 'igw', 3),
            self.monitors_with_mds_and('5monitor&2mds+2rgw', self.free, 5, 'rgw',  2),
            self.monitors_with_mds_and('5monitor&2mds+2igw', self.free, 5, 'igw',  2),
            self.monitors_with_mds_and('3monitor&2mds+4rgw', self.free, 3, 'rgw',  4),
            self.monitors_with_mds_and('3monitor&2mds+4igw', self.free, 3, 'igw',  4),
            self.monitors_xor('3monitor+4rgw', self.free, 3, 'rgw', 4),
            self.monitors_xor('3monitor+4igw', self.free, 3, 'igw', 4),
            self.monitors_2xor('3monitor+2rgw+2igw', self.free, 3, 'rgw', 'igw', 2, 2),
            self.monitors_with_mds_2xor('3monitor&2mds+2rgw+2igw', self.free, 3, 'rgw', 'igw', 2, 2),
        ]

