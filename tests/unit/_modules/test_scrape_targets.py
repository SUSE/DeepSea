import pytest
from srv.salt._modules import scrape_targets


@pytest.mark.parametrize(
    'targets, to_keep, total, expected',
    [
        ([1, 2, 3, 4, 5, 6], 1, 3, set([3, 4, 5, 6])),
        ([1, 2, 3, 4, 5, 6], 2, 3, set([1, 2, 5, 6])),
        ([1, 2, 3, 4, 5, 6], 3, 3, set([1, 2, 3, 4])),
        ([1, 2, 3, 4, 5], 1, 2, set([3, 4, 5])),
        ([1, 2, 3, 4, 5], 2, 2, set([1, 2])),
    ])
def test_partition_by_division(targets, to_keep, total, expected):
    res = scrape_targets._partition_by_division(targets, to_keep, total)
    err_report = 'unexpected partition result: {} vs {}'.format(res, expected)
    assert res == expected, err_report
