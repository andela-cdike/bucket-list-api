"""
Tests for the authentication endpoints
"""
import json
import os
import unittest

from flask import url_for

from api.app import create_app, db
from api.models import User
from helpers import create_api_headers


class TestAuthentication(unittest.TestCase):
    default_username = 'rikky_dyke'
    default_password = 'password'

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        user = User(username=self.default_username,
                    password=self.default_password)
        db.session.add(user)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @classmethod
    def tearDownClass(cls):
        pwd = os.getcwd()
        os.remove(pwd + '/bucketlistdb-test.sqlite')

    def test_api_requires_auth(self):
        response = self.client.get(url_for('api.get_bucketlists'),
                                   content_type='application/json')
        print response
        self.assertEquals(response.status_code, 401)

    def test_registration(self):
        """Tests user registration"""
        response = self.client.post(
            url_for('api.register'),
            headers=create_api_headers('rikky_dyke', 'password'),
            data=json.dumps({'username': 'itachi', 'password': 'password'}))
        self.assertEquals(response.status_code, 201)

    def test_registration_refuses_short_password(self):
        """
        Tests that passwords that are shorter than 6 characters are rejected
        """
        response = self.client.post(
            url_for('api.register'),
            headers=create_api_headers('rikky_dyke', 'password'),
            data=json.dumps({'username': 'itachi', 'password': 'pass'}))
        self.assertEquals(response.status_code, 400)

    def test_registration_refuses_blank_username(self):
        """Tests that blank usernames are rejected"""
        response = self.client.post(
            url_for('api.register'),
            headers=create_api_headers('rikky_dyke', 'password'),
            data=json.dumps({'username': '', 'password': 'pass'}))
        self.assertEquals(response.status_code, 400)

    def test_registration_of_non_unique_usernames(self):
        """Tests that api rejects usernames that are already taken"""
        response = self.client.post(
            url_for('api.register'),
            headers=create_api_headers('rikky_dyke', 'password'),
            data=json.dumps({'username': 'rikky_dyke',
                             'password': 'uchiha_madara'}))
        self.assertEquals(response.status_code, 400)

    def test_login(self):
        """Tests that login works"""
        response = self.client.post(
            url_for('api.login'),
            headers=create_api_headers('rikky_dyke', 'password'),
            data=json.dumps({'username': 'rikky_dyke',
                             'password': 'password'}))
        self.assertEquals(response.status_code, 200)

    def test_login_invalid_user(self):
        """Testst that login function rejects invalid users"""
        response = self.client.post(
            url_for('api.login'),
            headers=create_api_headers('rikky_dyke', 'password'),
            data=json.dumps({'username': 'rikimaru', 'password': 'senju'}))
        self.assertEquals(response.status_code, 401)

    def test_get_user(self):
        response = self.client.get(
            url_for('api.get_user', id=1),
            headers=create_api_headers('rikky_dyke', 'password'))
        self.assertEquals(response.status_code, 200)

    def test_that_invalid_routes_return_json(self):
        response = self.client.get(
            'auth/bucketlists/',
            headers=create_api_headers('rikky_dyke', 'password'))
        data = json.loads(response.get_data(as_text=True))
        self.assertEquals(response.status_code, 404)
        self.assertEquals(data['message'], '404: Not Found')

    def test_invalid_token_is_rejected(self):
        response = self.client.get(
            url_for('api.get_bucketlists'),
            headers=create_api_headers('token', ''))
        self.assertEquals(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
