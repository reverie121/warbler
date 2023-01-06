"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from urllib.parse import urlparse

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

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

        db.session.commit()


    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now that the session setting is saved
            # we can have the rest of our tests

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/users/1')

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

            messages = Message.query.filter(Message.user_id == 1)

            # Confirm new message is associated with user
            self.assertEqual(messages.count(), 1)

            redir_resp = c.post("/messages/new", data={"text": "Successfully Redirected"}, follow_redirects=True)
            html = redir_resp.get_data(as_text=True)

            # Confirm that it redirects to correct content
            self.assertEqual(redir_resp.status_code, 200)
            self.assertIn('Successfully Redirected', html)

    def test_show_message(self):
        """Does new message display properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            c.post("/messages/new", data={"text": "Hello"})

            resp = c.get("/messages/1")
            html = resp.get_data(as_text=True)

            # Make sure it loads the message detail page
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hello', html)


    def test_del_message(self):
        """Can user delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            c.post("/messages/new", data={"text": "Hello"})

            resp = c.post("/messages/1/delete")

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/users/1')

            c.post("/messages/new", data={"text": "Hello Again"})

            redir_resp = c.post("/messages/2/delete", follow_redirects=True)
            html = redir_resp.get_data(as_text=True)

            # Confirm that it redirects to correct content
            self.assertEqual(redir_resp.status_code, 200)
            self.assertIn('@testuser', html)

            messages = Message.query.filter(Message.user_id == 1)

            # Confirm message has been deleted
            self.assertEqual(messages.count(), 0)