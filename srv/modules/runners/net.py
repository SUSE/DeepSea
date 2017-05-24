# -*- coding: utf-8 -*-

import logging
import multiprocessing
import operator
import re
import salt.client
import time



from netaddr import IPNetwork, IPAddress

log = logging.getLogger(__name__)

def get_cpu_count(server):
    local = salt.client.LocalClient()
    #node, cpu_core = (local.cmd("S@"+server, 'grains.item',  ['num_cpus'], expr_form="compound")).popitem()
    result = local.cmd("S@"+server + " or " + server , 'grains.item',  ['num_cpus'], expr_form="compound")
    cpu_core = result.values()[0]['num_cpus']
    return cpu_core

def iperf(cluster = None, exclude = None, output = None, **kwargs):
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
    if cluster:
        search = "I@cluster:{}".format(cluster)

        if exclude_string:
            search += " and not ( " + exclude_string + " )"
            log.debug( "iperf: search {} ".format(search))

        public_networks = local.cmd(search , 'pillar.item', [ 'public_network' ], expr_form="compound")
        log.debug( "iperf: public_network {} ".format(public_networks))
        cluster_networks = local.cmd(search , 'pillar.item', [ 'cluster_network' ], expr_form="compound")
        log.debug( "iperf: cluster_network {} ".format(cluster_networks))
        total = local.cmd(search , 'grains.get', [ 'ipv4' ], expr_form="compound")
        log.debug( "iperf: total grains.get {} ".format(total))
        public_addresses = []
        cluster_addresses = []
        for host in sorted(total.iterkeys()):
            if 'public_network' in public_networks[host]:
                public_addresses.extend(_address(total[host], public_networks[host]['public_network']))
            if 'cluster_network' in cluster_networks[host]:
                cluster_addresses.extend(_address(total[host], cluster_networks[host]['cluster_network']))
            log.debug( "iperf: public_network {} ".format(public_addresses))
            log.debug( "iperf: cluster_network {} ".format(cluster_addresses))
        result = {}
        _create_server(public_addresses)
        p_result = _create_client(public_addresses)
        _create_server(cluster_addresses)
        c_result = _create_client(cluster_addresses)

        if output:
            result.update({'Public Network':p_result})
            result.update({'Cluster Network':c_result})
            return result
        else:
            sort_result = sorted(p_result.items(), key=operator.itemgetter(1))
            result.update({'Public Network':{ "Slowest 2 hosts" : dict(sort_result[:2]), "Fastest 2 hosts" : dict(sort_result[-2:]) }})
            sort_result = sorted(c_result.items(), key=operator.itemgetter(1))
            result.update({'Cluster Network':{ "Slowest 2 hosts" : dict(sort_result[:2]), "Fastest 2 hosts" : dict(sort_result[-2:]) }})
            return result
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
        _create_server(addresses)
        result = _create_client(addresses)
        #log.debug( "Sorted {} ".format( sorted( server_results.items(), key=operator.itemgetter(1))))
        if output:
            return result
        else:
            sort_result = sorted(result.items(), key=operator.itemgetter(1))
            return { "Slowest 2 hosts" : dict(sort_result[:2]), "Fastest 2 hosts" : dict(sort_result[-2:]) }

def _create_server(addresses):
    start_service = []
    local = salt.client.LocalClient()
    log.debug( "net.iperf._create_server: address list {} ".format(addresses) )
    for server in addresses:
        cpu_core = get_cpu_count(server)
        log.debug( "net.iperf._create_server: server {} cpu count {} ".format(server, cpu_core) )
        for x in range(cpu_core):
            log.debug( "net.iperf._create_server: server {} count {} port {} ".format(server, x, 5200+x ) )
            start_service.append( local.cmd( "S@"+server, 'multi.iperf_server_cmd', [ x, 5200+x ], expr_form="compound"))

def _create_client(addresses):
    results = []
    jid = []
    local = salt.client.LocalClient()
    for server in addresses: 
        cpu_core = get_cpu_count(server)
        log.debug( "net.iperf._create_client: server {} cpu count {} ".format(server, cpu_core) )
        clients = list(addresses)
        clients.remove(server)
        clients_size = len(clients)
        for x in xrange(0, cpu_core, clients_size):
            for y, client in enumerate(clients):
                log.debug( "net.iperf._create_client: server port num {}, num {} client {} to server {}".format(5200+x+y,x/clients_size, client, server) )
                if( x+y < cpu_core ):
    	            jid.append( local.cmd_async("S@"+client, 'multi.iperf', [server, x/clients_size, 5200+x+y ], expr_form="compound"))
                    log.debug( "net.iperf._create_client: actually called from {} to server {} with cpu {} port {} ".format(client, server, x/clients_size, 5200+x+y) )
        log.debug( "net.iperf._create_client: Server {} async iperf client count {}".format(server, len(jid)) )
        time.sleep(8)

    log.debug( "iperf: All Async iperf client count {}".format(len(jid)) )
    not_done = True
    while not_done:
        not_done = False
        for job in jid:
            if not __salt__['jobs.lookup_jid'](job):
                log.debug( "iperf: job not done {} ".format(job) )
                time.sleep(1)
                not_done = True
    results = []
    for job in jid:
            results.append( __salt__['jobs.lookup_jid'](job) )
    return _summarize_iperf( results ) 

def jumbo_ping(cluster = None, exclude = None, **kwargs):
    ping(cluster, exclude, ping_type="jumbo")

def ping(cluster = None, exclude = None, ping_type = None, **kwargs):
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
    if ping_type is "jumbo":
        results = local.cmd(search, 'multi.jumbo_ping', addresses, expr_form="compound")
    else:
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
        log.debug( "_address: ip {} in network {} ".format(address, network))
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

def _iperf_result_get_server(result):
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
	        server_results.update( {result[host]['server']:""} )
	        #server.update( {result[host]['server'],list()} )
            if result[host]['succeeded']:
                #print "success:\n{}".format(result[host]['succeeded']) 
                #print "filter:\n{}".format(result[host]['filter']) 
	        server_results[result[host]['server']] += " " + result[host]['filter']
            elif result[host]['failed']:
                #print "failed:\n{}".format(result[host]['failed']) 
		server_results[result[host]['server']] += " Failed to connect from {}".format(host)
            elif result[host]['errored']:
                #print "errored :\n{}".format(result[host]['errored']) 
		server_results[result[host]['server']] += " Error to connect from {}".format(host)

    for key, result in server_results.iteritems():
        total = 0
        speed = result.split('Mbits/sec')
	speed = filter(None, speed)
        try:
            for v in speed:
                total += float(v.strip())
            server_results[key] = str(total) + " Mbits/sec"
            #server_results[key] = str(total)
        except ValueError:
            continue 
    #log.debug( "Sorted {} ".format( sorted( server_results.items(), key=operator.itemgetter(1))))
    #return dict(sorted(server_results.items(), key=operator.itemgetter(1)))
    return server_results

    #return server_results

def _skip_dunder(settings):
    """
    Skip double underscore keys
    """
    return {k:v for k,v in settings.iteritems() if not k.startswith('__')}

