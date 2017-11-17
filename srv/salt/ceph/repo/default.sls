
nop:
  test.nop

{% if grains.get('os', '') == 'CentOS' %}

deepsea_centos_packages_repo:
  pkgrepo.managed:
    - name: deepsea_centos_packages_repo
    - humanname: DeepSea - CentoOS-$releasever Repo
    - baseurl: https://copr-be.cloud.fedoraproject.org/results/rjdias/home/epel-$releasever-$basearch/
    - gpgcheck: False
    - enabled: True
    - fire_event: True

{% endif %}