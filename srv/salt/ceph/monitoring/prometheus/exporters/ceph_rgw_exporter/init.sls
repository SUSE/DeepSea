
{% set osfinger = grains.get('osfinger') %}
{% set os = grains.get('os') %}
{% set osrelease = os + "-" + grains.get('osrelease') %}

{% set abspath = "/srv/salt/" + slspath %}
{% set custom = salt['pillar.get']('monitoring_prometheus_exporters_ceph_rgw_exporter', 'not a file') %}

include:
{% if salt['file.directory_exists'](abspath + "/" +  custom) %}
  - .{{ custom }}
{% elif salt['file.directory_exists'](abspath + "/" +  osfinger) %}
  - .{{ osfinger }}
{% elif salt['file.directory_exists'](abspath + "/" + osrelease) %}
  - .{{ osrelease }}
{% elif salt['file.directory_exists'](abspath + "/" + os) %}
  - .{{ os }}
{% else %}
  - .default
{% endif %}
