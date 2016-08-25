
SUSE_SLE-12-SP1_GA:
  module.run:
    - name: pkg.mod_repo
    - repo: SUSE_SLE-12-SP1_GA
    - kwargs: {
        baseurl: 'http://download.suse.de/ibs/SUSE:/SLE-12-SP1:/GA/standard',
        enabled: 'True'
        }
    - require_in:
        - pkg: install-ceph

SUSE_SLE-12_GA:
  module.run:
    - name: pkg.mod_repo
    - repo: SUSE_SLE-12_GA
    - kwargs: {
        baseurl: 'http://download.suse.de/ibs/SUSE:/SLE-12:/GA/standard/',
        enabled: 'True'
        }
    - require_in:
        - pkg: install-ceph

SUSE_SLE-12-SP1_Update:
  module.run:
    - name: pkg.mod_repo
    - repo: SUSE_SLE-12-SP1_Update
    - kwargs: {
        baseurl: 'http://download.suse.de/ibs/SUSE:/SLE-12-SP1:/Update/standard',
        enabled: 'True'
        }
    - require_in:
        - pkg: install-ceph

SUSE_SLE-12_Update:
  module.run:
    - name: pkg.mod_repo
    - repo: SUSE_SLE-12_Update
    - kwargs: {
        baseurl: 'http://download.suse.de/ibs/SUSE:/SLE-12:/Update/standard',
        enabled: 'True'
        }
    - require_in:
        - pkg: install-ceph

