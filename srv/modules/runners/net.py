# -*- coding: utf-8 -*-

import logging
import re
import salt.client

from netaddr import IPNetwork, IPAddress

log = logging.getLogger(__name__)

def ping(cluster = None, exclude = None, **kwargs):
    """
    Ping all addresses from all addresses on all minions.  If cluster is passed,
    restrict addresses to public and cluster networks.

    Note: Some optimizations could be done here in the multi module (such as
    skipping the source and destination when they are the same).  However, the
    unoptimized version is taking ~2.5 seconds on 18 minions with 72 addresses
    for success.  Failures take between 6 to 12 seconds.  Optimizations should
    focus there.

    TODO: Convert commented out print statements to log.debug

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
        print "Unsupported parameters: {}".format(" ,".join(extra_kwargs.keys()))
        text = re.sub(re.compile("^ {12}", re.MULTILINE), "", '''
            salt-run net.ping [cluster] [exclude]

            Ping all addresses from all addresses on all minions.
            If cluster is specified, restrict addresses to cluster and public networks.
            If exclude is specified, remove matching addresses.  See Salt compound matchers.
            within exclude individual ip address will be remove a specific target interface
            instead of ping from, the ping to interface will be removed


            Examples:
                salt-run net.ping
                salt-run net.ping ceph
                salt-run net.ping ceph L@mon1.ceph
                salt-run net.ping cluster=ceph exclude=L@mon1.ceph
                salt-run net.ping exclude=S@192.168.21.254
                salt-run net.ping exclude=S@192.168.21.0/29
                salt-run net.ping exclude="E@host*,host-osd-name*,192.168.1.1"
        ''')
        print text
        return


    local = salt.client.LocalClient()
    if cluster:
        search = "I@cluster:{}".format(cluster)
        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug( "ping: search {} ".format(search))
        networks = local.cmd(search , 'pillar.item', [ 'cluster_network', 'public_network' ], expr_form="compound")
        #print networks
        total = local.cmd(search , 'grains.get', [ 'ipv4' ], expr_form="compound")
        #print addresses
        addresses = []
        for host in sorted(total.iterkeys()):
            if 'cluster_network' in networks[host]:
                addresses.extend(_address(total[host], networks[host]['cluster_network']))
            if 'public_network' in networks[host]:
                addresses.extend(_address(total[host], networks[host]['public_network']))
    else:
        search = "*"
        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug( "ping: search {} ".format(search))
        addresses = local.cmd(search , 'grains.get', [ 'ipv4' ], expr_form="compound")

        addresses = _flatten(addresses.values())
        # Lazy loopback removal - use ipaddress when adding IPv6
        try:
            if addresses:
                addresses.remove('127.0.0.1')
            if exclude_iplist:
                for ex_ip in exclude_iplist:
                    log.debug( "ping: removing {} ip ".format(ex_ip))
                    addresses.remove(ex_ip)
        except ValueError:
            log.debug( "ping: remove {} ip doesn't exist".format(ex_ip))
            pass
    #print addresses
    results = local.cmd(search, 'multi.ping', addresses, expr_form="compound")
    #print results
    _summarize(len(addresses), results)

def _address(addresses, network):
    """
    Return all addresses in the given network

    Note: list comprehension vs. netaddr vs. simple
    """
    matched = []
    for address in addresses:
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

    log.debug( "_exclude_filter: excluding {}".format(excluded))
    excluded = excluded.split(",")
    log.debug( "_exclude_filter: split ',' {}".format(excluded))

    pattern_compound = re.compile("^.*([GPIJLNSE]\@).*$")
    pattern_iplist = re.compile( "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$" )
    pattern_ipcidr = re.compile( "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$")
    pattern_hostlist = re.compile( "^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]).)*([A-Za-z]|[A-Za-z][A-Za-z0-9-]*[A-Za-z0-9])$")
    compound = []
    ipcidr = []
    iplist = []
    hostlist = []
    regex_list = []
    for para in excluded:
        if pattern_compound.match(para):
            log.debug( "_exclude_filter: Compound {}".format(para))
            compound.append(para)
        elif pattern_iplist.match(para):
            log.debug( "_exclude_filter: ip {}".format(para))
            iplist.append(para)
        elif pattern_ipcidr.match(para):
            log.debug( "_exclude_filter: ipcidr {}".format(para))
            ipcidr.append("S@"+para)
        elif pattern_hostlist.match(para):
            hostlist.append("L@"+para)
            log.debug( "_exclude_filter: hostname {}".format(para))
        else:
            regex_list.append("E@"+para)
            log.debug( "_exclude_filter: not sure but likely Regex host {}".format(para))

    #if ipcidr:
    #    log.debug("_exclude_filter ip subnet is not working yet ... = {}".format(ipcidr))
    new_compound_excluded = " or ".join(compound + hostlist + regex_list + ipcidr)
    log.debug("_exclude_filter new formed compound excluded list = {}".format(new_compound_excluded))
    if new_compound_excluded and iplist:
         return new_compound_excluded, iplist
    elif new_compound_excluded:
         return new_compound_excluded, None
    elif iplist:
         return None, iplist
    else:
         return None, None

def _flatten(l):
    """
    Flatten a array of arrays
    """
    log.debug( "_flatten: {}".format(l))
    return list(set(item for sublist in l for item in sublist))

def _summarize(total, results):
    """
    Summarize the successes, failures and errors across all minions
    """
    success = []
    failed = []
    errored = []
    slow = []
    log.debug( "_summarize: results {}".format(results))
    for host in sorted(results.iterkeys()):
        if results[host]['succeeded'] == total:
            success.append(host)
        if 'failed' in results[host]:
            failed.append("{} from {}".format(results[host]['failed'], host))
        if 'errored' in results[host]:
            errored.append("{} from {}".format(results[host]['errored'], host))
        if 'slow' in results[host]:
            slow.append("{} from {} average rtt {}".format(results[host]['slow'], host, "{0:.2f}".format(results[host]['avg'])))


    if success:
        avg = sum( results[host].get('avg') for host in results) / len(results)
    else:
        avg = 0

    print "Succeeded: {} addresses from {} minions average rtt {} ms".format(total, len(success), "{0:.2f}".format(avg))
    if slow:
       print "Warning: \n    {}".format("\n    ".join(slow))
    if failed:
        print "Failed: \n    {}".format("\n    ".join(failed))
    if errored:
       print "Errored: \n    {}".format("\n    ".join(errored))

def _skip_dunder(settings):
    """
    Skip double underscore keys
    """
    return {k:v for k,v in settings.iteritems() if not k.startswith('__')}

