from ext_lib.utils import runner


def update():
    foo = runner(__opts__)
    foo.cmd('mon.update')
    foo.cmd('mgr.update')
    foo.cmd('osd.update')


def deploy(demo=False):
    print("may check for updates before")
    print("Call to ceph-iscsi")
    print("Call to mds")
    print("Call to nfs-ganesha")
    print("Call to rgw")
