#-*- coding: utf8 -*-
'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
from random import randrange

import pytest

from tests.factories import SearchFilterFactory, UserFactory, SubFactory
from tests.test_api_non_workspaced_base import ReadOnlyAPITests, OBJECT_COUNT
from tests.test_api_agent import logout, http_req
from tests.conftest import login_as
from faraday.server.models import SearchFilter


from faraday.server.api.modules.search_filter import SearchFilterView


@pytest.mark.usefixtures('logged_user')
class TestSearchFilterAPI(ReadOnlyAPITests):
    model = SearchFilter
    factory = SearchFilterFactory
    api_endpoint = 'searchfilter'
    view_class = SearchFilterView

    pytest.fixture(autouse=True)

    def test_list_retrieves_all_items_from(self, test_client):
        return

    def test_list_retrieves_all_items_from_logger_user(self, test_client, session, logged_user):
        user_filter = SearchFilterFactory.create(creator=logged_user)
        session.add(user_filter)
        session.commit()
        res = test_client.get(self.url())
        assert res.status_code == 200
        if 'rows' in res.json:
            assert len(res.json['rows']) == 1
        else:
            assert len(res.json) == 1

    def test_retrieve_one_object(self):
        return

    def test_retrieve_one_object_from_logged_user(self, test_client, session, logged_user):

        filters = []
        for n in range(5):
            user_filter = SearchFilterFactory.create(creator=logged_user)
            session.add(user_filter)
            filters.append(user_filter)

        session.commit()
        
        print(self.url(filters[randrange(5)]))
        res = test_client.get(self.url(filters[randrange(5)]))
        assert res.status_code == 200
        assert isinstance(res.json, dict)

    def test_retrieve_filter_from_another_user(self, test_client, session, logged_user):
        user_filter = SearchFilterFactory.create(creator=logged_user)
        another_user = UserFactory.create() 
        session.add(user_filter)
        session.add(another_user)
        session.commit()

        logout(test_client, [302])
        login_as(test_client, another_user)

        res = test_client.get(self.url(user_filter))
        assert res.status_code == 404

    def test_retrieve_filter_list_is_empty_from_another_user(self, test_client, session, logged_user):
        user_filter = SearchFilterFactory.create(creator=logged_user)
        another_user = UserFactory.create() 
        session.add(user_filter)
        session.add(another_user)
        session.commit()

        logout(test_client, [302])
        login_as(test_client, another_user)

        res = test_client.get(self.url())
        assert res.status_code == 200
        assert res.json == []

    def test_delete_filter_from_another_user(self, test_client, session, logged_user):
        user_filter = SearchFilterFactory.create(creator=logged_user)
        another_user = UserFactory.create() 
        session.add(user_filter)
        session.add(another_user)
        session.commit()

        logout(test_client, [302])
        login_as(test_client, another_user)

        res = test_client.delete(self.url(user_filter))
        assert res.status_code == 404