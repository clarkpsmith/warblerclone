from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes
from sqlalchemy import exc


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

db.create_all()


class MessageModelTestCase(TestCase):
    """test message model"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user = User.signup(
            username="user1", email="user1@gmail.com", password="password", image_url=None)
        user.id = 1000
        self.user_id = user.id

        db.session.commit()

        message = Message(text="Test Message", user_id=1000)
        message.id = 2000
        self.message_id = message.id
        db.session.add(message)
        db.session.commit()

        self.user1 = User.query.get(self.user_id)

        like = Likes(user_id=self.user1.id, message_id=self.message_id)
        like.id = 2000
        self.like_id = like.id
        db.session.add(like)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """delete test client and sample data"""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """test basic message model"""

        m = Message(text="Test Message 2", user_id=1000)
        m.id = 1111
        m_id = m.id
        db.session.add(m)
        db.session.commit()
        message = Message.query.get(m_id)
        self.assertEqual(message.text, "Test Message 2")
        self.assertEqual(message.user_id, 1000)
        self.assertEqual(len(self.user1.messages), 2)

    def test_like_model(self):
        """ test basic like model"""

        like = Likes.query.get(self.like_id)
        self.assertEqual(like.user_id, self.user_id)
        self.assertEqual(like.message_id, self.message_id)
        self.assertEqual(len(self.user1.likes), 1)
