{% include 'ceph/cluster/' + grains['id'] + '.sls' ignore missing %}

{% include 'ceph/deepsea_minions.sls' ignore missing %}
{% include 'ceph/blacklist.sls' ignore missing %}
{% include 'ceph/disk_led.sls' ignore missing %}
{% include 'ceph/minions/' + grains['id'] + '.sls' ignore missing %}
{% include 'ceph/global.yml' ignore missing %}
{% include 'ceph/internal.yml' ignore missing %}

