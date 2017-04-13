from srv.modules.runners import orderednodes


class TestOrderedNodes():
    """
    Make sure we return the <list> in expected order.
    """

    def test__preserve_order_sorted(self):
        inp = ['mon1', 'mon2', 'mon3', 'data1', 'data2',
               'data2', 'data3', 'mds1', 'mon1', 'mon3', 'rgw1']
        expect = ['mon1', 'mon2', 'mon3', 'data1',
                  'data2', 'data3', 'mds1', 'rgw1']
        assert orderednodes._preserve_order_sorted(inp) == expect
