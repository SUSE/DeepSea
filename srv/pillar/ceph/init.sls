


{% include 'ceph/cluster/' + grains['fqdn'] + '.sls' ignore missing %}

{% include 'ceph/master_minion.sls' ignore missing %}

{% include 'ceph/rgw.sls' ignore missing %}



