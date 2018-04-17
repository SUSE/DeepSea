
{% include 'ceph/cluster/' + grains['id'] + '.sls' ignore missing %}

{% include 'ceph/deepsea_minions.sls' ignore missing %}


