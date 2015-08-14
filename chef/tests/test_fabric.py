import mock

from chef.fabric import chef_roledefs
from chef.tests import ChefTestCase, mockSearch

class FabricTestCase(ChefTestCase):
    @mock.patch('chef.search.Search')
    def test_roledef(self, MockSearch):
        search_data = {
            ('role', '*:*'): {},
        }
        search_mock_memo = {}
        def search_mock(index, q='*:*', *args, **kwargs):
            data = search_data[index, q]
            search_mock_inst = search_mock_memo.get((index, q))
            if search_mock_inst is None:
                search_mock_inst = search_mock_memo[index, q] = mock.Mock()
                search_mock_inst.data = data
            return search_mock_inst
        MockSearch.side_effect = search_mock
        print(MockSearch('role').data)
        

    @mockSearch({('role', '*:*'): {1:2}})
    def test_roledef2(self, MockSearch):
        print(MockSearch('role').data)
