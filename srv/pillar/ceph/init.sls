
{% include 'ceph/cluster/' + grains['id'] + '.sls' ignore missing %}

{% include 'ceph/master_minion.sls' ignore missing %}

{% include 'ceph/deepsea_minions.sls' ignore missing %}


