{% if salt['saltutil.runner']('validate.discovery', cluster='ceph') == False %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}

push proposals:
  salt.runner:
    - name: push.proposal

refresh_pillar1:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
    - require:
      - salt: push proposals

post configuration:
  salt.runner:
    - name: configure.cluster
    - require: 
      - salt: refresh_pillar1

refresh_pillar2:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
    - require: 
      - salt: post configuration

{% for role in [ 'admin', 'mon', 'mgr', 'osd', 'igw', 'mds', 'rgw', 'ganesha', 'openattic'] %}
{{ role }} key:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.{{ role }}.key
    - failhard: True

{% endfor %}

setup monitoring:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.monitoring

setup node exporters:
  salt.state:
    - tgt: '*'
    - sls: ceph.monitoring.prometheus.exporters.node_exporter

