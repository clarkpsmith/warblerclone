"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()


class UserModelTestCase(TestCase):
    """Test user model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup(
            username="user1", email="user1@gmail.com", password="password", image_url=None)
        user1.id = 1000
        user1_id = user1.id
        user2 = User.signup(
            username="user2", email="user2@gmail.com", password="password", image_url=None)
        user2.id = 2000
        user2_id = user2.id

        db.session.commit()

        self.user1 = User.query.get(user1_id)
        self.user2 = User.query.get(user2_id)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u.id = 3000
        u_id = u.id
        db.session.add(u)
        db.session.commit()
        user = User.query.get(u_id)

        # User should have no messages & no followerss
        self.assertEqual(len(user.messages), 0)
        self.assertEqual(len(user.followers), 0)
        self.assertEqual(user.email, "test@test.com")

    def test__repr__(self):
        self.assertEqual(self.user1.__repr__(),
                         f"<User #{self.user1.id}: {self.user1.username}, {self.user1.email}>")

    def test_is_followed_by(self):
        self.user2.followers.append(self.user1)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user2.following), 0)

    def test_valid_signup(self):
        user_test = User.signup(
            "user_test", "user_test@gmail.com", "password", None)
        user_test.id = 3000
        user_test_id = user_test.id
        db.session.commit()
        test_user = User.query.get(user_test_id)
        self.assertIsNotNone(test_user)
        self.assertEqual(test_user.username, "user_test")
        self.assertEqual(test_user.email, "user_test@gmail.com")
        self.assertNotEqual(test_user.password, "password")
        self.assertTrue(test_user.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        user_test = User.signup(
            "user1", "user_test@gmail.com", "password", None)
        user_test.id = 4000
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        user_test = User.signup(
            "user3", None, "password", None)

        user_test.id = 4000
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):

        with self.assertRaises(ValueError) as context:
            user_test = User.signup(
                "user3", "user_test@gmail.com", "", None)

        with self.assertRaises(ValueError) as context:
            user_test = User.signup(
                "user3", "user_test@gmail.com", None, None)

    def test_valid_authentication(self):

        good_username = User.authenticate("user1", "password")
        self.assertEqual(self.user1, good_username)

    def test_invalid_password(self):
        self.assertFalse(User.authenticate("user1", "piggies"))

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("user7", "password"))
