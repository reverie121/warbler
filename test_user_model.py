"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


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


class UserModelTestCase(TestCase):
    """Test views for users."""

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

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # Does the repr method work as expected?
        self.assertEqual(repr(u), '<User #3: testuser, test@test.com>')

    def test_following_functions(self):
        """Do the is_following and is_followed_by User methods work?"""

        u1_follows_u2 = Follows(user_being_followed_id=2, user_following_id=1)

        db.session.add(u1_follows_u2)
        db.session.commit()

        u1 = User.query.get(1)
        u2 = User.query.get(2)

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))

        self.assertTrue(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))
    
    def test_user_signup(self):
        """Does the User signup method work?"""
        
        User.signup(username='signup_user', email='signup_user@email.com', password='password', image_url=None)

        try:
            User.signup(username='failed_signup_user', email='signup_user@email.com')
        except:
            no_password = 'failed'
        
        signup_users = db.session.query(User).filter(User.username.contains('signup'))

        self.assertEqual(signup_users.count(), 1)
        self.assertEqual(no_password, 'failed')
    
    def test_user_authenticate(self):
        """Does the User authenticate method work?"""

        User.signup(username='signup_user', email='signup_user@email.com', password='password', image_url=None)

        user = User.authenticate('signup_user', 'password')

        self.assertIsInstance(user, User)

        failed_username = User.authenticate('wrong', 'password')
        failed_password = User.authenticate('signup_user', 'wrong')

        self.assertFalse(failed_username)
        self.assertFalse(failed_password)