
{% set master = salt['master.minion']() %}

{% if salt['saltutil.runner']('validate.discovery', cluster='ceph') == False %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ master }}
    - failhard: True

{% endif %}

push proposals:
  salt.runner:
    - name: push.proposal

refresh_pillar1:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.refresh

show networks:
  salt.runner:
    - name: advise.networks

{% for role in [ 'admin', 'osd', 'mon', 'mgr', 'igw', 'mds', 'rgw', 'ganesha'] %}
{{ role }} key:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.{{ role }}.key
    - failhard: True

{% endfor %}

populate node scrape configs:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.populate_node_scrape_configs

install prometheus:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.install

distribute node scrape configs:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.push_node_scrape_configs

install and setup node exporters:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.node_exporter

advise OSDs:
  salt.runner:
    - name: advise.osds

install grafana:
  salt.state:
    - tgt: 'I@roles:grafana and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.grafana

# setup grafana auth:
#   salt.state:
#     - tgt: {{ salt['pillar.get']('master_minion') }}
#     - sls: ceph.monitoring.grafana.auth
# 
# setup grafana dashboards:
#   salt.state:
#     - tgt: {{ salt['pillar.get']('master_minion') }}
#     - sls: ceph.monitoring.grafana.dashboards
# 
