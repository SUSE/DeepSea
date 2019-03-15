
metapackage install nop:
  test.nop

{% if grains.get('osfullname', '') == 'SLES' %}
metapackage for salt versioning:
  pkg.installed:
    - pkgs:
      - ses-release
{% endif %}
