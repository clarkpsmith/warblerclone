"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 1000
        self.testuser_id = self.testuser.id
        db.session.commit()

    def tearDown(self):

        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message(self):
        """Can users add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            res = c.post("/messages/new",
                         data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_unauthorized_add_message(self):
        """test if unauthorized users can add a message"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            res = c.post("/messages/new",
                         data={"text": "Hello"}, follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_message_show(self):
        """show a message"""
        m = Message(id=2000, text="test2",
                    timestamp=None, user_id=self.testuser_id)
        db.session.add(m)
        db.session.commit()

        message = Message.query.get(2000)
        with self.client as client:
            res = client.get(f'/messages/{message.id}')
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("test2", html)

    def test_message_wrongid_show(self):
        """test showing a messageid thats not in the database"""
        with self.client as client:
            res = client.get('/messages/9999')
            self.assertEqual(res.status_code, 404)

    def test_messages_destroy(self):
        """delete a message"""
        m = Message(id=2000, text="test2",
                    timestamp=None, user_id=self.testuser_id)
        db.session.add(m)
        db.session.commit()
        message = Message.query.get(2000)
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        res = c.post(f'/messages/{message.id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        msg = Message.query.get(2000)
        self.assertFalse(msg)

    def test_unauthorized_message_destroy(self):
        """delete a message"""
        m = Message(id=2000, text="test2",
                    timestamp=None, user_id=self.testuser_id)
        db.session.add(m)
        db.session.commit()
        message = Message.query.get(2000)
        with self.client as c:
            res = c.post(
                f'/messages/{message.id}/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_wronguser_message_destroy(self):
        """delete a message"""
        m = Message(id=2000, text="test2",
                    timestamp=None, user_id=self.testuser_id)
        db.session.add(m)
        db.session.commit()
        message = Message.query.get(2000)
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 48392085
            res = c.post(
                f'/messages/{message.id}/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)
