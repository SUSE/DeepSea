{% set require_osd_release = salt['osd.require_osd_release']() %}
{% if require_osd_release and require_osd_release != 'nautilus' %}
require_osd_release is not nautilus:
  test.fail_without_changes:
    - name: |
        'require-osd-release' is currently '{{ require_osd_release }}',
        but must be set to 'nautilus' before upgrading to SES 7.
        Please run `ceph osd require-osd-release nautilus` to fix this
        before proceeding further.
    - failhard: True
{% endif %}

{% if grains.get('oscodename', '') != 'SUSE Linux Enterprise Server 15 SP2' %}

not running sle 15 sp2:
  test.fail_without_changes:
    - name: |
        This host is not running SUSE Linux Enterprise Server 15 SP2.
        Please upgrade the operating system first, before running the adopt process.
    - failhard: True

{% endif %}

# This check is so we bail out in case of a half upgraded system (for example,
# if someone runs `zypper dup` with both SES6 and SES7 repos available, they'll
# potentially still have ceph nautilus installed, which we really don't want).
# TODO: figure out how to print a friendly error message in this case
ceph must be octopus if installed:
  cmd.run:
    - name: "[ ! -x /usr/bin/ceph ] || ceph --version | grep -q 'ceph version 15'"
    - failhard: True

{% set ses7_container_image = salt['pillar.get']('ses7_container_image', 'registry.suse.com/ses/7/ceph/ceph') %}

cephadm:
  pkg.installed:
    - pkgs:
      - cephadm
      - podman

# TODO: may need to support authenticated registries. For more details see:
# - https://github.com/ceph/ceph-salt/pull/277
# - https://tracker.ceph.com/issues/44886
/etc/containers/registries.conf:
  file.managed:
    - source:
        - salt://ceph/upgrade/ses7/files/registries.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - makedirs: True
    - backup: minion
    - failhard: True

pull ceph container image:
  cmd.run:
    - name: "cephadm --image {{ ses7_container_image }} pull"
    - unless: "podman images | grep -q {{ ses7_container_image }}"
    - failhard: True

adopt ceph daemons:
  cmd.run:
    - name: |
        for DAEMON in $(cephadm ls|jq -r '.[] | select(.style=="legacy") | .name'); do
            case $DAEMON in
                mon*|mgr*|osd*)
                    cephadm --image {{ ses7_container_image }} adopt --skip-pull --style legacy --force-start --name $DAEMON
                    ;;
            esac
        done
    - unless: "[ -z \"$(cephadm ls|jq -r '.[] | select(.style==\"legacy\") | .name')\" ]"
    - failhard: True
