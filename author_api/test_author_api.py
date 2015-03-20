from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from models import (
    Author,
    FriendRelationship,
    FriendRequest,
    FollowerRelationship)

import uuid

from rest_api import scaffold

c = scaffold.SocialAPIClient()

# Values to be inserted and checked in the Author model
GITHUB_USERNAME = "gituser"
BIO = "This is my witty biography!"
HOST = "http://example.com/"

# Values to be inserted and checked in the User model
# required User model attributes
USERNAME = "nameuser"
PASSWORD = uuid.uuid4()

# optional User model attributes
FIRST_NAME = "firstname"
LAST_NAME = "lastname"
EMAIL = "person@example.org"

# Main user in the tests
USER = {
    'username':USERNAME,
    'first_name':FIRST_NAME,
    'last_name':LAST_NAME,
    'email':EMAIL,
    'password':PASSWORD }

# For friend, follower, and request model testing
USER_A = {'username':"User_A", 'password':uuid.uuid4()}
USER_B = {'username':"User_B", 'password':uuid.uuid4()}

class AuthorModelAPITests(APITestCase):
    """
    Basic testing of the Author model creation and database insertion
    """
    def setUp(self):
        """
        Creates 3 users and 3 authors.

        The main user/author is user/author.
        Secondary user/authors are user_a/user_details_a and user_b/user_details_b

        Relationships are created in their respective tests
        """
        self.user = User.objects.create_user(**USER)
        self.user_a = User.objects.create_user(**USER_A)
        self.user_b = User.objects.create_user(**USER_B)
        self.author = Author.objects.create(
            user = self.user,
            github_username = GITHUB_USERNAME,
            bio = BIO,
            host = HOST)
        self.author_a = Author.objects.create(
            user = self.user_a,
            github_username = GITHUB_USERNAME,
            bio = BIO,
            host = HOST)
        self.author_b = Author.objects.create(
            user = self.user_b,
            github_username = GITHUB_USERNAME,
            bio = BIO,
            host = HOST)

        c.token_credentials(self.author)

    def tearDown(self):
        """Remove all created objects from mock database"""
        Author.objects.all().delete()
        User.objects.all().delete()
        FriendRelationship.objects.all().delete()
        FriendRequest.objects.all().delete()
        FollowerRelationship.objects.all().delete()
        c.credentials()

    def test_set_up(self):
        """ Assert that that the user model was created in setUp()"""
        try:
            user = User.objects.get(username = USERNAME)
        except:
            self.assertFalse(True, 'Error retrieving %s from database' %USERNAME)

        self.assertEquals(user.first_name, FIRST_NAME)
        self.assertEquals(user.last_name, LAST_NAME)
        self.assertEquals(user.email, EMAIL)

    def test_retrieve_details(self):
        # Reg. unauthenticated client from APITestCase
        response = self.client.get('/author/%s' % self.author.id,
            content_type="application/json")

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data['email'], EMAIL)

    def test_invalid_retrieve_details(self):
        response = c.get('/author/no_user_here')
        self.assertEquals(response.status_code, 404)

    def test_relation_user_dne(self):
        response = c.get('/author/friends/%s' %'bogus_user')
        self.assertEquals(response.status_code, 404)

    def test_retrieve_friends(self):
        friendors = [self.author_a, self.author_b]
        scaffold.create_friends(self.author, friendors, create_post = False)

        response = c.get('/author/friends/%s' %self.author.id)
        self.assertEquals(response.status_code, 200)
        scaffold.authors_in_relation(self, response.data['friendors'], friendors)

    def test_retrieve_requests(self):
        requestors = [self.author_a, self.author_b]
        scaffold.create_requestors(self.author, requestors)

        response = c.get('/author/friendrequests/%s' %self.author.id)

        self.assertEquals(response.status_code, 200)
        scaffold.authors_in_relation(self, response.data['requestors'], requestors)

    def test_retrieve_followers(self):
        followers = [self.author_a, self.author_b]
        scaffold.create_followers(self.author, followers)

        response = c.get('/author/followers/%s' %self.author.id)
        self.assertEquals(response.status_code, 200)
        scaffold.authors_in_relation(self, response.data['followers'], followers)