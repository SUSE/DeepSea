{% for role in [ 'mon', 'osd', 'igw', 'mds', 'rgw' ] %}

salt.state:
 - tgt: {{ salt['pillar.get']('master_minion') }}
 - tgt_type: compound
 - sls: ceph.{{ role }}.restart
 - failhard: True

{% endfor %}
