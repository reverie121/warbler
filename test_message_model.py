"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User(username = 'user1', email='user1@email.com', password='password')

        u2 = User(username = 'user2', email='user2@email.com', password='password')

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(user_id=1, text='This is a test message.')

        db.session.add(m)
        db.session.commit()

        message = Message.query.first()

        self.assertEqual(message.user.username, 'user1')
        self.assertEqual(message.text, 'This is a test message.')

        # Does the repr method work as expected?
        self.assertEqual(repr(message), '<Message #1 made by user #1>')
