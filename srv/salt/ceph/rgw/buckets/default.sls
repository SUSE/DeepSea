
install rgw:
  pkg.installed:
    - pkgs:
      - python-boto

{% for user in salt['rgw.users']('rgw') %}
create demo bucket for {{ user }}:
  module.run:
    - name: rgw.create_bucket
    - kwargs:
        'bucket_name': {{ user }}-demo
        'host': {{ salt['pillar.get']('rgw_host') }}
        'access_key': {{ salt['rgw.access_key'](user) }}
        'secret_key': {{ salt['rgw.secret_key'](user) }}
        'ssl': {{ salt['pillar.get']('rgw_ssl') }}
        'port': {{ salt['pillar.get']('rgw_port') }}
{% endfor %}
