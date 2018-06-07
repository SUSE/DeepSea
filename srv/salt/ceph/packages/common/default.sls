


stage prep dependencies:
  pkg.installed:
    - pkgs:
      - gptfdisk
    - fire_event: True

{% if grains.get('osfullname', '') == 'SLES' %}

install ses-realease package:
  pkg.installed:
    - pkgs:
      - ses-release

{% endif %}


