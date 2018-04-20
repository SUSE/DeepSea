
{% set service = 'mds' %}
{% set test_node = salt.saltutil.runner('select.one_minion', cluster='ceph', roles=service) %}

{% include slspath + '/common.sls' %}
