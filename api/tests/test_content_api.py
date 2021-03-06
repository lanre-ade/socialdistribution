from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from ..models.author import Author, CachedAuthor
from ..models.content import Post, Comment
from ..utils import scaffold
from api_settings import settings
import uuid
import os

# Values to be inserted and checked in the Author model
USERNAME = "programmer"
GITHUB_USERNAME = "programmer"
BIO = "This is my witty biography!"
HOST = settings.HOST

# Values to be inserted and checked in the User model
# required User model attributes

USER_A = {"username":"User_A", "password":uuid.uuid4()}
USER_B = {"username":"User_B", "password":uuid.uuid4()}
USER_C = {"username":"User_C", "password":uuid.uuid4()}
USER_D = {"username":"User_D", "password":uuid.uuid4()}
USER_E = {"username":"User_E", "password":uuid.uuid4()}

# optional User model attributes
FIRST_NAME = "Jerry"
LAST_NAME = "Maguire"
EMAIL = "jmaguire@smi.com"
PASSWORD = str(uuid.uuid4())

# Post attributes
TEXT = "Some post text"

AUTHOR_PARAMS = {
    'github_username':GITHUB_USERNAME,
    'bio':BIO,
    'host':HOST
}


class ContentAPITestCase(TestCase):
    """
    Testing Content API Prototypes
    """
    def setUp(self):
        self.user_a, self.author_a, self.client = scaffold.create_authenticated_author(USER_A,
            AUTHOR_PARAMS)

        self.user_b, self.author_b = scaffold.create_author(USER_B, AUTHOR_PARAMS)
        self.user_c, self.author_c = scaffold.create_author(USER_C, AUTHOR_PARAMS)

        self.post = Post.objects.create(content = TEXT,
            author = self.author_a, visibility="PUBLIC")

        self.no_auth = scaffold.SocialAPIClient()

    def tearDown(self):
        """Remove all created objects from mock database"""
        Author.objects.all().delete()
        User.objects.all().delete()
        Post.objects.all().delete()
        Token.objects.all().delete()

        self.client.credentials()

    def test_set_up(self):
        """Assert that that the models were created in setUp()"""
        try:
            user = User.objects.get(username=USER_A["username"])
            User.objects.get(id=self.user_a.id)
        except:
            self.assertFalse(True, "Error retrieving %s from database" %USER_A["username"])
        try:
            Post.objects.get(guid=self.post.guid)
        except:
            self.assertFalse(True, "Error retrieving post %s from database" %self.post.guid)


    def test_get_post_by_author_from_db(self):
        """Post created in setUp() can be retrieved using Author id from setUp()"""
        post = Post.objects.get(author = self.author_a)
        self.assertEquals(post.content, TEXT)

    def test_get_post(self):
        response = self.client.get('/post/%s' % self.post.guid)
        print vars(response)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data["source"], settings.HOST, "Not setting source properly")
        self.assertEquals(response.data["origin"], settings.HOST, "Not setting origin properly")
        scaffold.assertPostAuthor(self, response.data, self.author_a)
        # scaffold.pretty_print(response.data)

    def test_get_multiple_posts_by_author_with_http(self):
        # Create two posts, in addition to the post created in setUp()
        scaffold.create_multiple_posts(self.author_a, 2, ptext = TEXT)

        a_id = self.author_a.id
        response = self.client.get("/author/%s/posts" %a_id)

        self.assertEquals(response.status_code, 200)
        scaffold.assertNumberPosts(self, response.data, 3)

    def test_get_posts_of_friends(self):
        # This test should only return posts by author_a and not his friends
        # This creates friends and their posts (two posts in total)
        scaffold.create_friends(self.author_a, [self.author_b, self.author_c], create_post = True, visibility="FRIENDS")

        a_id = self.author_a.id
        response = self.client.get("/author/%s/posts" % a_id)
        self.assertEquals(response.status_code, 200)

        posts = response.data
        # scaffold.pretty_print(response.data)
        scaffold.assertNumberPosts(self, posts, 1)
        scaffold.assertPostAuthor(self, posts["posts"][0], self.author_a)

    def test_get_posts_of_fof(self):
        # Add Friends and a post each
        scaffold.create_friends(self.author_a, [self.author_b], create_post = True, visibility="FOAF")

        # Create friend of friend and a post
        user, author = scaffold.create_author(USER_D, AUTHOR_PARAMS)
        scaffold.create_friends(self.author_b, [author], create_post = True, visibility="FOAF")

        # author_a should be able to retrieve posts by author created above
        aid = author.id
        response = self.client.get("/author/%s/posts" % aid)
        self.assertEquals(response.status_code, 200)

        # scaffold.pretty_print(response.data)

        scaffold.assertNumberPosts(self, response.data, 1)
        scaffold.assertPostAuthor(self, response.data["posts"][0], author)

    def test_attempt_get_posts_of_fof(self):
        # Add Friends and a post each
        scaffold.create_friends(self.author_a, [self.author_b], create_post = True, visibility="FOAF")

        # Create friend of friend and a post with Friends-only permissions
        user, author = scaffold.create_author(USER_D, AUTHOR_PARAMS)
        scaffold.create_multiple_posts(author, num = 1, visibility="FOAF")

        # author_a should not be able to retrieve post by author created above
        aid = author.id

        response = self.client.get("/author/%s/posts" %aid)
        self.assertEquals(response.status_code, 403)

    # def test_get_posts_in_private_list(self):
    #     # Add Posts
    #     _acl = {"permissions":500, "shared_users":[str(self.author_a.id)]}
    #     scaffold.create_multiple_posts(self.author_b, num = 1, acl = _acl)
    #
    #     bid = self.author_b.id
    #     response = self.client.get("/author/%s/posts" %bid)
    #
    #     # scaffold.pretty_print(response.data)
    #
    #     self.assertEquals(response.status_code, 200)
    #     scaffold.assertPostAuthor(self, response.data[0], self.author_b)
    #     scaffold.assertSharedUser(self, response.data[0], self.author_a)
    #
    # def test_attempt_get_posts_in_private_list(self):
    #     # Add Posts
    #     _acl = {"permissions":500, "shared_users":[str(self.author_c.id)]}
    #     scaffold.create_multiple_posts(self.author_b, num = 2, acl = _acl)
    #
    #     bid = self.author_b.id
    #     response = self.client.get("/author/%s/posts" %bid)
    #     self.assertEquals(response.status_code, 403)

    def test_get_private_post_again(self):
        # Add Posts
        scaffold.create_multiple_posts(self.author_a, num = 2, visibility = "PRIVATE")

        aid = self.author_a.id
        response = self.client.get("/author/%s/posts" %aid)
        self.assertEquals(response.status_code, 200)

        # scaffold.pretty_print(response.data)
        scaffold.assertNumberPosts(self, response.data, 3)
        #
        # # TODO this is a bug. At least one post should be returned
        # # Create user to attempt to retrieve private posts
        # user, author, client = scaffold.create_authenticated_author(USER_D, AUTHOR_PARAMS)
        # response = client.get("/author/%s/posts" %aid)
        #
        # scaffold.assertNumberPosts(self, response.data, 1)
        #

    def test_attempt_get_private_post(self):
        # Add Posts
        scaffold.create_multiple_posts(self.author_b, num = 2, visibility = "PRIVATE")

        bid = self.author_b.id
        response = self.client.get("/author/%s/posts" %bid)
        self.assertEquals(response.status_code, 403)

    def test_create_post(self):
        ptext = TEXT + " message"
        post = {
            "title": "Tst Post",
            "content": ptext,
            "contentType": "text/x-markdown",
            "visibility": scaffold.ACL_DEFAULT
        }

        response = self.client.post("/post", post)
        self.assertEquals(response.status_code, 201)

        # Retrieve post manually to confirm
        post = Post.objects.get(guid = response.data["guid"])
        if not post:
            self.assertFalse(True, "Post does not exist")

        self.assertEquals(post.content, ptext, "wrong post text")
        self.assertEquals(post.author.id, self.author_a.id, "wrong user")

    def test_create_public_post_with_image(self):
        user, author, client = scaffold.create_authenticated_author(USER_E, AUTHOR_PARAMS)
        base64image = scaffold.get_image_base64(os.path.dirname(__file__) + '/fixtures/images/s.jpg')
        post = {"image": "data:image/jpeg;base64," + base64image,
            "title": "Tst Post",
            "content": TEXT,
            "contentType": "text/x-markdown",
            "visibility": scaffold.ACL_DEFAULT
        }
        response = self.client.post("/post", post, format='multipart')
        self.assertEquals(response.status_code, 201)
        # Get the image.
        self.assertEquals(response.data.get('image'), post['image'])

    def test_create_post_no_auth(self):
        ptext = TEXT + " message"
        post = {
            "content": ptext,
            "visibility": scaffold.ACL_DEFAULT,
        }

        response = self.no_auth.post('/post', post)
        self.assertEquals(response.status_code, 401)

    # def test_attempt_set_read_only_fields(self):
        # """Read only fields should be ignored in POST request"""
        # acl = {"permissions":300, "shared_users":["user_a"]}
        # post = {"content":TEXT, "id":4, "date":"2015-01-01",
            # "acl":acl}

        # response = self.client.post("/author/post", post)
        # self.assertEquals(response.status_code, 201)
        # self.assertTrue(response.data["guid"] != 4, "ID was set; should not have been")

    def test_create_blank_post(self):
        """Should not be able to create post with no text"""
        response = self.client.post("/post", {})
        self.assertEquals(response.status_code, 400)

    def test_public_post_set(self):
        """public and fof are False by default"""
        post = Post.objects.create(
          content = TEXT,
          author = self.author_a,
          visibility = scaffold.ACL_DEFAULT
        )
        self.assertEquals(post.visibility, scaffold.ACL_DEFAULT)

    def test_create_public_post_http(self):
        post = {
          "title": "Public Post",
          "contentType": "text/plain",
          "content": TEXT,
          "visibility": scaffold.ACL_DEFAULT
        }
        response = self.client.post("/post", post)

        self.assertEquals(response.status_code, 201)

    def test_delete_post(self):
        post = Post.objects.create(content=TEXT, author = self.author_a, visibility=scaffold.ACL_DEFAULT)

        postid = post.guid

        response = self.client.delete('/post/%s' % postid)
        self.assertEquals(response.status_code, 204)

        # ensure post has been removed
        try:
            Post.objects.get(guid=postid)
            self.assertTrue(False, "Post should not exist still")
        except:
            pass

    def test_attempt_delete_post_non_author(self):
        post = Post.objects.create(content = TEXT, author = self.author_b, visibility = scaffold.ACL_DEFAULT)
        # deny user a's request
        response = self.client.delete('/post/%s' % post.guid)
        self.assertEquals(response.status_code, 403)

    def test_add_comment_to_public_post(self):
        post = Post.objects.create(content=TEXT, author = self.author_b, visibility = scaffold.ACL_DEFAULT)

        postid = post.guid

        # comment on the post
        comment = {
          "comment": TEXT,
          "contentType": "text/x-markdown"
        }

        response = self.client.post('/post/%s/comments' % postid, comment)
        # s.pretty_print(response.data)
        self.assertEquals(response.status_code, 201)

        commentid = response.data['guid']

        # get the comment by author_a and ensure its associated post is postid
        comment = Comment.objects.get(guid = commentid)
        self.assertEquals(comment.post.guid, postid, "comment post fk does not match")
        self.assertEquals(comment.author.user.username, self.author_a.user.username)

    def test_delete_comment_by_comment_author(self):
        post, comment = scaffold.create_post_with_comment(
            self.author_b, self.author_a, scaffold.ACL_DEFAULT, TEXT, TEXT)

        cid = comment.guid

        response = self.client.delete('/post/%s/comments/%s' % (post.guid, cid))
        self.assertEquals(response.status_code, 204)

        # ensure comment has been removed
        try:
            comment = Comment.objects.get(guid=cid)
            self.assertTrue(False, "Comment was not deleted")
        except:
            pass

    def test_attempt_delete_comment_post_author(self):
        post, comment = scaffold.create_post_with_comment(
            self.author_b, self.author_a, scaffold.ACL_DEFAULT, TEXT, TEXT)

        cid = comment.guid
        pid = post.guid

        # delete the comment (by post author)
        response = self.client.delete('/post/%s/comments/%s' % (pid, cid))
        self.assertEquals(response.status_code, 204)

        # ensure comment has been removed
        try:
            comment = Comment.objects.get(guid=cid)
            self.assertTrue(False, "Comment was not deleted")
        except:
            pass

        # Post should still exist
        try:
            post = Post.objects.get(id = pid)
            self.assertEquals(post.author.user.id, self.author_a.user.id)
            self.assertTrue(False, "Post was deleted and should not be")
        except:
            pass

    def test_get_post_with_comments(self):
        post, comment = scaffold.create_post_with_comment(
            self.author_a, self.author_b, scaffold.ACL_DEFAULT, TEXT, TEXT)

        pid = post.guid

        # Create one more comment
        Comment.objects.create(post = post, comment = TEXT, author = self.author_c)

        # get the post
        response = self.client.get('/post/%s' % (pid))
        self.assertEquals(response.status_code, 200)

        # scaffold.pretty_print(response.data)

        scaffold.assertPostAuthor(self, response.data, self.author_a)
        scaffold.assertNumberComments(self, response.data, 2)
        scaffold.assertAuthorsInComments(self, [self.author_b, self.author_c],
            response.data['comments'])

    def test_retrieve_timeline_own(self):
        response = self.client.get('/author/posts')
        self.assertEquals(response.status_code, 200)

        # scaffold.pretty_print(response.data)
        post = response.data["posts"][0]

        self.assertEquals(len(response.data), 1)
        scaffold.assertPostContent(self, post, unicode(TEXT))
        scaffold.assertPostAuthor(self, post, self.author_a)

    def test_retrieve_multiple_posts_timeline(self):
        # Test the retrieval of multiple posts in the timeline
        scaffold.create_multiple_posts(self.author_a, num = 5)

        response = self.client.get('/author/posts')
        self.assertEquals(response.status_code, 200)

        # scaffold.pretty_print(response.data)

        scaffold.assertNumberPosts(self, response.data, 6)
        scaffold.assertNoRepeatGuids(self, response.data['posts'])

    # def test_timeline_includes_friends(self):
    #     scaffold.create_friends(self.author_a, [self.author_b, self.author_c], create_post = True)
    #
    #     response = self.client.get('/author/posts')
    #     self.assertEquals(response.status_code, 200)
    #
    #     authors = [
    #         self.author_a,
    #         self.author_b,
    #         self.author_c ]
    #
    #     self.assertEquals(len(response.data), 3)
    #     scaffold.pretty_print(response.data)
    #     scaffold.assertAuthorsInPosts(self, authors, response.data)
    #
    # def test_timeline_include_fof(self):
    #     scaffold.create_friends(self.author_a, [self.author_b, self.author_c], create_post = True)
    #
    #     # Create a friend of friend for author b
    #     user, author = scaffold.create_author(USER_D, AUTHOR_PARAMS)
    #     scaffold.create_friends(self.author_b, [author], create_post = True)
    #
    #     response = self.client.get('/author/posts')
    #     self.assertEquals(response.status_code, 200)
    #
    #     scaffold.pretty_print(response.data)
    #     self.assertEquals(len(response.data), 4)
    #
    #     authors = [
    #         self.author_a,
    #         self.author_b,
    #         self.author_c,
    #         author ]
    #
    #     scaffold.assertAuthorsInPosts(self, authors, response.data)

    def test_retrieve_timeline_bogus_user(self):
        response = self.no_auth.get('/author/posts')
        self.assertEquals(response.status_code, 401)
