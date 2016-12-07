
{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% set client = "client." + role %}
{% set keyring_file = salt['keyring.file']('rgw', client)  %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ client }} -i {{ keyring_file }}"

{% endfor %}


