# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error,unused-argument
# pylint: skip-file

"""
Network utilities
"""

from __future__ import absolute_import
from __future__ import print_function
import time
import logging
import operator
import re
# pylint: disable=import-error,3rd-party-module-not-gated
from netaddr import IPNetwork, IPAddress
import ipaddress
import pprint
# pylint: disable=relative-import
# pylint: disable=import-error,3rd-party-module-not-gated,blacklisted-external-import,blacklisted-module
from six.moves import range
# pylint: disable=incompatible-py3-code

log = logging.getLogger(__name__)

try:
    import salt.client
except ImportError:
    log.error('Could not import salt.client')

try:
    import salt.ext.six as six
except ImportError:
    log.error('Could not import salt.ext.six')


def help_():
    """
    Usage
    """
    usage = ('salt-run net.get_cpu_count server=minion\n\n'
             '    Returns the number of cpus for a minion\n'
             '\n\n'
             'salt-run net.ping:\n'
             'salt-run net.ping ceph:\n'
             'salt-run net.ping cluster=ceph:\n'
             'salt-run net.ping exclude=target:\n\n'
             '    Summarizes network connectivity between minion interfaces\n'
             '\n\n'
             'salt-run net.jumbo_ping:\n\n'
             '    Summarizes network connectivity between minion interfaces for jumbo packets\n'
             '\n\n'
             'salt-run net.iperf:\n'
             'salt-run net.iperf ceph:\n'
             'salt-run net.iperf cluster=ceph:\n'
             'salt-run net.iperf exclude=target:\n\n'
             '    Summarizes bandwidth throughput between minion interfaces\n'
             '\n\n')
    print(usage)
    return ""


def get_cpu_count(server):
    """
    Returns the number of cpus for the server
    """
    local = salt.client.LocalClient()
    result = local.cmd("S@{} or {}".format(server, server),
                       'grains.item', ['num_cpus'], tgt_type="compound")
    cpu_core = list(result.values())[0]['num_cpus']
    return cpu_core


def iperf(cluster=None, exclude=None, output=None, **kwargs):
    """
    iperf server created from the each minions and then clients are created
    base on the server's cpu count and request that number of other minions
    as client to hit the server and report the total bendwidth.

    CLI Example: (Before DeepSea with a cluster configuration)
    .. code-block:: bash
        sudo salt-run net.iperf

    or you can run it with exclude
    .. code-block:: bash
        sudo salt-run net.iperf exclude="E@host*,host-osd-name*,192.168.1.1"

    (After DeepSea with a cluster configuration)
    .. code-block:: bash
        sudo salt-run net.iperf cluster=ceph

    To get all host iperf result
        sudo salt-run net.iperf cluster=ceph output=full

    """
    exclude_string = exclude_iplist = None
    if exclude:
        exclude_string, exclude_iplist = _exclude_filter(exclude)

    addresses = []
    local = salt.client.LocalClient()
    # Salt targets can use list or string
    if cluster:
        search = "I@cluster:{}".format(cluster)

        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug("iperf: search {} ".format(search))

        public_networks = local.cmd(search, 'pillar.item',
                                    ['public_network'], tgt_type="compound")

        ipversion = 'ipv4'
        log.info("public networks:\n{}".format(pprint.pformat(public_networks)))
        for host in public_networks:
            if 'public_network' in public_networks[host]:
                ipversion = _ipversion(public_networks[host]['public_network'])
                break

        log.debug("iperf: public_network {} ".format(public_networks))
        cluster_networks = local.cmd(search, 'pillar.item',
                                     ['cluster_network'], tgt_type="compound")
        log.debug("iperf: cluster_network {} ".format(cluster_networks))
        total = local.cmd(search, 'grains.get', [ipversion], tgt_type="compound")
        log.debug("iperf: total grains.get {} ".format(total))
        public_addresses = []
        cluster_addresses = []
        for host in sorted(six.iterkeys(total)):
            if 'public_network' in public_networks[host]:
                public_addresses.extend(
                    _address(total[host],
                             public_networks[host]['public_network']))
            if 'cluster_network' in cluster_networks[host]:
                cluster_addresses.extend(
                    _address(total[host],
                             cluster_networks[host]['cluster_network']))
            log.debug("iperf: public_network {} ".format(public_addresses))
            log.debug("iperf: cluster_network {} ".format(cluster_addresses))
        result = {}
        _create_server(public_addresses)
        p_result = _create_client(public_addresses)
        _create_server(cluster_addresses)
        c_result = _create_client(cluster_addresses)
        p_sort = _add_unit(sorted(list(p_result.items()),
                                  key=operator.itemgetter(1), reverse=True))
        c_sort = _add_unit(sorted(list(c_result.items()),
                                  key=operator.itemgetter(1), reverse=True))

        if output:
            result.update({'Public Network': p_sort})
            result.update({'Cluster Network': c_sort})
            return result
        else:
            result.update({'Public Network':
                           {"Slowest 2 hosts": p_sort[-2:],
                            "Fastest 2 hosts": p_sort[:2]}})
            result.update({'Cluster Network':
                           {"Slowest 2 hosts": c_sort[-2:],
                            "Fastest 2 hosts": c_sort[:2]}})
            return result
    else:
        # pylint: disable=redefined-variable-type
        search = __utils__['deepsea_minions.show']()
        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug("ping: search {} ".format(search))

        public_networks = local.cmd(search, 'pillar.item',
                                    ['public_network'], tgt_type="compound")

        ipversion = 'ipv4'
        log.info("public networks:\n{}".format(pprint.pformat(public_networks)))
        for host in public_networks:
            if 'public_network' in public_networks[host]:
                ipversion = _ipversion(public_networks[host]['public_network'])
                break

        addresses = local.cmd(search, 'grains.get',
                              [ipversion], tgt_type="compound")
        addresses = _flatten(list(addresses.values()))
        # Lazy loopback removal - use ipaddress when adding IPv6
        try:
            if ipversion == 'ipv4':
                addresses.remove('127.0.0.1')
            elif ipversion == 'ipv6':
                addresses.remove('::1')
                addresses = [addr for addr in addresses if not addr.startswith("fe80")]
            if exclude_iplist:
                for ex_ip in exclude_iplist:
                    log.debug("ping: removing {} ip ".format(ex_ip))
                    addresses.remove(ex_ip)
        except ValueError:
            log.debug("ping: remove {} ip doesn't exist".format(ex_ip))
        _create_server(addresses)
        result = _create_client(addresses)
        sort_result = _add_unit(sorted(list(result.items()),
                                       key=operator.itemgetter(1),
                                       reverse=True))
        if output:
            return sort_result
        else:
            return {"Slowest 2 hosts": sort_result[-2:],
                    "Fastest 2 hosts": sort_result[:2]}


def _add_unit(records):
    """
    Add formatting
    """
    stuff = []
    for host in enumerate(records):
        log.debug("Host {} Speed {}".format(host[1][0], host[1][1]))
        stuff.append([host[1][0], "{} Mbits/sec".format(host[1][1])])
    return stuff


def _create_server(addresses):
    """
    Start iperf server
    """
    start_service = []
    local = salt.client.LocalClient()
    log.debug("net.iperf._create_server: address list {} ".format(addresses))
    for server in addresses:
        cpu_core = get_cpu_count(server)
        log.debug("net.iperf._create_server: server {} cpu count {} "
                  .format(server, cpu_core))
        for count in range(cpu_core):
            log.debug("net.iperf._create_server: server {} count {} port {} "
                      .format(server, count, 5200+count))
            start_service.append(local.cmd("S@{}".format(server),
                                           'multi.iperf_server_cmd',
                                           [count, 5200+count], tgt_type="compound"))


def _create_client(addresses):
    """
    Start iperf client
    """
    results = []
    jid = []
    local = salt.client.LocalClient()
    for server in addresses:
        cpu_core = get_cpu_count(server)
        log.debug("net.iperf._create_client: server {} cpu count {} "
                  .format(server, cpu_core))
        clients = list(addresses)
        clients.remove(server)
        clients_size = len(clients)
        # pylint: disable=invalid-name
        for x in range(0, cpu_core, clients_size):
            # pylint: disable=invalid-name
            for y, client in enumerate(clients):
                log.debug("net.iperf._create_client:")
                log.debug("server port:{}, x:{} client:{} to server:{}"
                          .format(5200+x+y, x/clients_size, client, server))
                if x+y < cpu_core:
                    jid.append(
                        local.cmd_async(
                            "S@"+client,
                            'multi.iperf',
                            [server, x/clients_size, 5200+x+y],
                            tgt_type="compound"))
                    log.debug("net.iperf._create_client:")
                    log.debug("calling from client:{} ".format(client))
                    log.debug("to server:{} ".format(server))
                    log.debug("cpu:{} port:{}".format(x/clients_size, 5200+x+y))
        log.debug("net.iperf._create_client:")
        log.debug("Server {} iperf client count {}".format(server, len(jid)))
        time.sleep(8)

    log.debug("iperf: All Async iperf client count {}".format(len(jid)))
    not_done = True
    while not_done:
        not_done = False
        for job in jid:
            if not __salt__['jobs.lookup_jid'](job):
                log.debug("iperf: job not done {} ".format(job))
                time.sleep(1)
                not_done = True
    results = []
    for job in jid:
        results.append(__salt__['jobs.lookup_jid'](job))
    return _summarize_iperf(results)


def jumbo_ping(cluster=None, exclude=None, **kwargs):
    """
    Ping with larger packets
    """
    ping(cluster, exclude, ping_type="jumbo")


def ping(cluster=None, exclude=None, ping_type=None, **kwargs):
    """
    Ping all addresses from all addresses on all minions.  If cluster is passed,
    restrict addresses to public and cluster networks.

    Note: Some optimizations could be done here in the multi module (such as
    skipping the source and destination when they are the same).  However, the
    unoptimized version is taking ~2.5 seconds on 18 minions with 72 addresses
    for success.  Failures take between 6 to 12 seconds.  Optimizations should
    focus there.

    CLI Example: (Before DeepSea with a cluster configuration)
    .. code-block:: bash
        sudo salt-run net.ping

    or you can run it with exclude
    .. code-block:: bash
        sudo salt-run net.ping exclude="E@host*,host-osd-name*,192.168.1.1"

    (After DeepSea with a cluster configuration)
    .. code-block:: bash
        sudo salt-run net.ping cluster=ceph
        sudo salt-run net.ping ceph

    """
    exclude_string = exclude_iplist = None
    if exclude:
        exclude_string, exclude_iplist = _exclude_filter(exclude)

    extra_kwargs = _skip_dunder(kwargs)
    if _skip_dunder(kwargs):
        print("Unsupported parameters:{}".format(" ,".join(list(extra_kwargs.keys()))))
        text = re.sub(re.compile("^ {12}", re.MULTILINE), "", '''
            salt-run net.ping [cluster] [exclude]

            Ping all addresses from all addresses on all minions.
            If cluster is specified, restrict addresses to cluster networks.
            If exclude is specified, remove matching addresses.
            Detail read the Salt compound matchers.
            All the excluded individual ip address interface will be removed,
            instead of ping from, the ping to interface will be removed.


            Examples:
                salt-run net.ping
                salt-run net.ping ceph
                salt-run net.ping ceph L@mon1.ceph
                salt-run net.ping cluster=ceph exclude=L@mon1.ceph
                salt-run net.ping exclude=S@192.168.21.254
                salt-run net.ping exclude=S@192.168.21.0/29
                salt-run net.ping exclude="E@host*,host-osd-name*,192.168.1.1"
        ''')
        print(text)
        return ""

    local = salt.client.LocalClient()
    if cluster:
        search = "I@cluster:{}".format(cluster)
        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug("ping: search {} ".format(search))
        networks = local.cmd(search, 'pillar.item',
                             ['cluster_network', 'public_network'],
                             tgt_type="compound")

        ipversion = 'ipv4'
        log.info("networks:\n{}".format(pprint.pformat(networks)))
        for host in networks:
            if 'public_network' in networks[host]:
                ipversion = _ipversion(networks[host]['public_network'])
                break

        total = local.cmd(search, 'grains.get', [ipversion], tgt_type="compound")
        addresses = []
        for host in sorted(six.iterkeys(total)):
            if 'cluster_network' in networks[host]:
                addresses.extend(_address(total[host],
                                          networks[host]['cluster_network']))
            if 'public_network' in networks[host]:
                addresses.extend(_address(total[host],
                                          networks[host]['public_network']))
    else:
        # pylint: disable=redefined-variable-type
        search = __utils__['deepsea_minions.show']()

        hosts = local.cmd(search, 'pillar.item',
                             ['public_network'],
                             tgt_type="compound")

        ipversion = 'ipv4'
        for host in hosts:
            if 'public_network' in hosts[host]:
                ipversion = _ipversion(hosts[host]['public_network'])
                break

        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug("ping: search {} ".format(search))
        addresses = local.cmd(search, 'grains.get',
                              [ipversion], tgt_type="compound")

        addresses = _flatten(list(addresses.values()))
        # Lazy loopback removal - use ipaddress when adding IPv6
        try:
            if addresses:
                if ipversion == 'ipv4':
                    addresses.remove('127.0.0.1')
                elif ipversion == 'ipv6':
                    addresses.remove('::1')
                    addresses = [addr for addr in addresses if not addr.startswith("fe80")]
                else:
                    raise RuntimeError("Neither IPv4 nor IPv6")
                log.info("addresses:\n{}".format(pprint.pformat(addresses)))
            if exclude_iplist:
                for ex_ip in exclude_iplist:
                    log.debug("ping: removing {} ip ".format(ex_ip))
                    addresses.remove(ex_ip)
        except ValueError:
            log.debug("ping: remove {} ip doesn't exist".format(ex_ip))
    if ping_type == "jumbo":
        results = local.cmd(search, 'multi.jumbo_ping',
                            addresses, tgt_type="compound")
    else:
        results = local.cmd(search, 'multi.ping',
                            addresses, tgt_type="compound")
    _summarize(len(addresses), results)
    return ""


def _ipversion(_network):
    """
    Return the address version
    """
    try:
        network = ipaddress.ip_network(u'{}'.format(_network))
    except ValueError as err:
        log.error("Invalid network {}".format(err))
        return 'ipv4'
    if network.version == 6:
        return 'ipv6'
    return 'ipv4'


def _address(addresses, network):
    """
    Return all addresses in the given network

    Note: list comprehension vs. netaddr vs. simple
    """
    matched = []
    for address in addresses:
        log.debug("_address: ip {} in network {} ".format(address, network))
        if IPAddress(address) in IPNetwork(network):
            matched.append(address)
    return matched


def _exclude_filter(excluded):
    """
    Internal exclude_filter return string in compound format

    Compound format = {'G': 'grain', 'P': 'grain_pcre', 'I': 'pillar',
                       'J': 'pillar_pcre', 'L': 'list', 'N': None,
                       'S': 'ipcidr', 'E': 'pcre'}
    IPV4 address = "255.255.255.255"
    hostname = "myhostname"
    """

    log.debug("_exclude_filter: excluding {}".format(excluded))
    excluded = excluded.split(",")
    log.debug("_exclude_filter: split ',' {}".format(excluded))

    pattern_compound = re.compile(r"^.*([GPIJLNSE]\@).*$")
    pattern_iplist = re.compile(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}" +
        r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
    pattern_ipcidr = re.compile(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}" +
        r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])" +
        r"(\/([0-9]|[1-2][0-9]|3[0-2]))$")
    pattern_hostlist = re.compile(
        r"^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]).)*" +
        r"([A-Za-z]|[A-Za-z][A-Za-z0-9-]*[A-Za-z0-9])$")
    compound = []
    ipcidr = []
    iplist = []
    hostlist = []
    regex_list = []
    for para in excluded:
        if pattern_compound.match(para):
            log.debug("_exclude_filter: Compound {}".format(para))
            compound.append(para)
        elif pattern_iplist.match(para):
            log.debug("_exclude_filter: ip {}".format(para))
            iplist.append(para)
        elif pattern_ipcidr.match(para):
            log.debug("_exclude_filter: ipcidr {}".format(para))
            ipcidr.append("S@"+para)
        elif pattern_hostlist.match(para):
            hostlist.append("L@"+para)
            log.debug("_exclude_filter: hostname {}".format(para))
        else:
            regex_list.append("E@"+para)
            log.debug("_exclude_filter: Regex host? {}".format(para))

    # if ipcidr:
    #    log.debug("_exclude_filter ip subnet not working = {}".format(ipcidr))
    new_compound_excluded = " or ".join(
        compound + hostlist + regex_list + ipcidr)
    log.debug("{}".format(new_compound_excluded))
    log.debug("{}".format(new_compound_excluded))
    if new_compound_excluded and iplist:
        return new_compound_excluded, iplist
    elif new_compound_excluded:
        return new_compound_excluded, None
    elif iplist:
        return None, iplist
    return None, None


def _flatten(_list):
    """
    Flatten a array of arrays
    """
    log.debug("_flatten: {}".format(_list))
    return list(set(item for sublist in _list for item in sublist))


def _summarize(total, results):
    """
    Summarize the successes, failures and errors across all minions
    """
    success = []
    failed = []
    errored = []
    slow = []
    log.debug("_summarize: results {}".format(results))
    for host in sorted(six.iterkeys(results)):
        if results[host]['succeeded'] == total:
            success.append(host)
        if 'failed' in results[host]:
            failed.append("{} from {}".format(results[host]['failed'], host))
        if 'errored' in results[host]:
            errored.append("{} from {}".format(results[host]['errored'], host))
        if 'slow' in results[host]:
            slow.append("{} from {} average rtt {}".format(
                results[host]['slow'], host,
                "{0:.2f}".format(results[host]['avg'])))

    if success:
        avg = sum(results[host].get('avg') for host in results) / len(results)
    else:
        avg = 0

    print("Succeeded: {} addresses from {} minions average rtt {} ms".format(
        total, len(success), "{0:.2f}".format(avg)))
    if slow:
        print("Warning: \n    {}".format("\n    ".join(slow)))
    if failed:
        print("Failed: \n    {}".format("\n    ".join(failed)))
    if errored:
        print("Errored: \n    {}".format("\n    ".join(errored)))


def _iperf_result_get_server(result):
    """
    Return server results
    """
    return result['server']


def _summarize_iperf(results):
    """
    iperf summarize the successes, failures and errors across all minions
    """
    server_results = {}
    log.debug("Results {} ".format(results))
    for result in results:
        for host in result:
            log.debug("Server {}".format(result[host]['server']))
            if not result[host]['server'] in server_results:
                server_results.update({result[host]['server']: ""})
            if result[host]['succeeded']:
                log.debug("filter:\n{}".format(result[host]['filter']))
                server_results[result[host]['server']] +=\
                        " " + result[host]['filter']
                log.debug("Speed {}".
                          format(server_results[result[host]['server']]))
            elif result[host]['failed']:
                log.debug("failed:\n{}".format(result[host]['failed']))
                server_results[result[host]['server']] +=\
                        " Failed to connect from {}".format(host)
            elif result[host]['errored']:
                log.debug("errored :\n{}".format(result[host]['errored']))
                server_results[result[host]['server']] +=\
                        " {} iperf error check installation.".format(host)

    for key, result in six.iteritems(server_results):
        total = 0
        speed = result.split('Mbits/sec')
        speed = [_f for _f in speed if _f]
        try:
            for value in speed:
                total += float(value.strip())
            # server_results[key] = str(total) + " Mbits/sec"
            server_results[key] = int(total)
        except ValueError:
            continue
    return server_results


def _skip_dunder(settings):
    """
    Skip double underscore keys
    """
    return {k: v for k, v in six.iteritems(settings) if not k.startswith('__')}

__func_alias__ = {
                 'help_': 'help',
                 }
