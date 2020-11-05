from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, User, Message, Follows, Likes
from sqlalchemy import exc

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


db.create_all()

# disable CSRF token verification
app.config['WTF_CSRF_ENABLED'] = False


class TestUserViews(TestCase):
    """test user views"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        # add user data
        user = User.signup(
            username="user1", email="user1@gmail.com", password="password", image_url=None)
        user.id = 1000
        self.user_id = user.id
        user2 = User.signup(
            username="user2", email="user2@gmail.com", password="password", image_url=None)
        user2.id = 2000
        self.user2_id = user2.id
        db.session.commit()

        # add message data
        message = Message(text="Test Message", user_id=self.user2_id)
        message.id = 2000
        self.message_id = message.id
        db.session.add(message)
        db.session.commit()

        # add following data
        follow = Follows(user_being_followed_id=self.user2_id,
                         user_following_id=self.user_id)
        db.session.add(follow)
        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_index(self):
        """test users page"""

        with app.test_client() as client:
            res = client.get("/users")
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("<p>@user1</p>", html)
            self.assertIn("<p>@user2</p>", html)

    def test_user_search(self):
        """ test users search page"""

        with app.test_client() as client:
            res = client.get("/users?q=user1")
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("<p>@user1</p>", html)

    def test_user_show(self):
        """test user show"""

        with app.test_client() as client:
            res = client.get(f'/users/{self.user2_id}')
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Test Message", html)
            self.assertIn("@user2", html)

    def test_show_following(self):
        """ test show following """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.get(
                f'/users/{self.user_id}/following', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("<p>@user2</p>", html)

    def test_show_followers(self):
        """ test show followers"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.get(
                f'/users/{self.user2_id}/followers', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("<p>@user1</p>", html)

    def test_add_follow(self):
        """test adding a follow"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2_id
            res = client.post(
                f'/users/follow/{self.user_id}', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("<p>@user1</p>", html)

    def test_unauthorized_following(self):
        """ test unauthorized following """
        with app.test_client() as client:
            res = client.post(
                f'/users/follow/{self.user_id}', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_stop_following(self):
        """test stop following"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.post(
                f'/users/stop-following/{self.user2_id}', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            user = User.query.get(self.user_id)
            self.assertEqual(len(user.following), 0)

    def test_unauthorized_stop_following(self):
        """ test unauthorized following """
        with app.test_client() as client:
            res = client.post(
                f'/users/stop-following/{self.user2_id}', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_show_update_profile(self):
        """test show update profile page"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.get('/users/profile')
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Edit this user!", html)

    def test_update_profile(self):
        """test show update profile page"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.post('/users/profile', follow_redirects=True, data={
                              "username": "user1", "email": "user1@gmail.com", "password": "password", "location": "Boulder"})
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Boulder", html)

    def test_unauthorized_update_profile(self):
        """test show update profile page"""
        with app.test_client() as client:
            res = client.get('/users/profile', follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_like(self):
        """test liking a post"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.post(
                f"/users/add_like/{self.message_id}", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("fa fa-thumbs-up", html)
            self.assertEqual(len(Likes.query.all()), 1)

    def set_up_likes(self):
        """set up likes"""
        like = Likes(user_id=self.user_id, message_id=self.message_id)
        like.id = 4000
        self.like_id = like.id
        db.session.add(like)
        db.session.commit()

    def test_remove_like(self):
        """remove already liked post"""
        self.set_up_likes()
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.post(
                f"/users/remove_like/{self.message_id}", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertFalse(Likes.query.get(self.like_id))

    def test_unauthorized_like(self):
        """test liking a post"""
        with app.test_client() as client:
            res = client.post(
                f"/users/add_like/{self.message_id}", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_unauthorized_remove_like(self):
        """remove already liked post"""

        like = Likes(user_id=self.user_id, message_id=self.message_id)
        db.session.add(like)
        db.session.commit()
        with app.test_client() as client:
            res = client.post(
                f"/users/remove_like/{self.message_id}", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_show_liked_posts(self):
        """show liked for posts for user"""
        self.set_up_likes()
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.get(f"/users/{self.user_id}/likes")
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("fa fa-thumbs-up", html)
            self.assertIn("Test Message", html)

    def test_show_unauthorized_liked_posts(self):
        """show liked for posts for user"""
        self.set_up_likes()
        with app.test_client() as client:
            res = client.get(
                f"/users/{self.user_id}/likes", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_delete_user(self):
        """test delete profile """
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id
            res = client.post('/users/delete', follow_redirects=True)
            user = User.query.get(self.user_id)
            self.assertFalse(user)
