"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase
from urllib.parse import urlparse

from models import db, connect_db, Message, User, Follows, Likes

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


class UserViewTestCase(TestCase):
    """Test views for users."""

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
    
    def test_logout(self):
        """Does the logout route work?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            # Now that the session setting is saved
            # we can have the rest of our tests         

            resp = c.get('/logout')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/login')


    def test_user_list(self):
        """Does the user list display properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
            db.session.add(testuser2)
            db.session.commit()

            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)
            self.assertIn('@testuser2', html)
        
    def test_user_search(self):
        """Does the user list search display properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            searcheduser = User.signup(username="searcheduser",
                                    email="search@test.com",
                                    password="searcheduser",
                                    image_url=None)
            db.session.add(searcheduser)
            db.session.commit()

            resp = c.get("/users?q=searcheduser")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@searcheduser', html)
            self.assertNotIn('@testuser', html)
    
    def test_user_profile(self):
        """Does the user profile display properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            resp = c.get("/users/1")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)

    def test_user_follows(self):
        """Do the following and followers user pages display properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            followeruser = User.signup(username="followeruser",
                                    email="follower@test.com",
                                    password="followeruser",
                                    image_url=None)
            db.session.add(followeruser)
            db.session.commit()

            new_follow = Follows(user_being_followed_id=1, 
                                user_following_id=2)
            db.session.add(new_follow)
            db.session.commit()

            following_resp = c.get("/users/2/following")
            following_html = following_resp.get_data(as_text=True)

            followers_resp = c.get("/users/1/followers")
            followers_html = followers_resp.get_data(as_text=True)

            # Check for presence of follower and followed by user in both pages
            self.assertEqual(following_resp.status_code, 200)
            self.assertIn('@testuser', following_html)
            self.assertIn('@followeruser', following_html)

            self.assertEqual(followers_resp.status_code, 200)
            self.assertIn('@testuser', followers_html)
            self.assertIn('@followeruser', followers_html)

            # Remove follower and check again
            follow = Follows.query.first()
            db.session.delete(follow)
            db.session.commit()

            following_resp = c.get("/users/2/following")
            following_html = following_resp.get_data(as_text=True)

            followers_resp = c.get("/users/1/followers")
            followers_html = followers_resp.get_data(as_text=True)

            # testuser should not be present
            self.assertEqual(following_resp.status_code, 200)
            self.assertNotIn('@testuser', following_html)
            self.assertIn('@followeruser', following_html)

            # followeruser should not be present
            self.assertEqual(followers_resp.status_code, 200)
            self.assertIn('@testuser', followers_html)
            self.assertNotIn('@followeruser', followers_html)

            # Log out for remaining assertions
            c.get('/logout')

            following_resp = c.get("/users/2/following")
            followers_resp = c.get("/users/1/followers")

            # Routes should redirect to root
            self.assertEqual(following_resp.status_code, 302)
            self.assertEqual(urlparse(following_resp.location).path, '/')
            self.assertEqual(followers_resp.status_code, 302)
            self.assertEqual(urlparse(following_resp.location).path, '/')


    def test_add__remove_follow(self):
            """Do the routes for adding and removing a follow work?"""

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
            
            followeduser = User.signup(username="followeduser",
                                    email="followed@test.com",
                                    password="followeduser",
                                    image_url=None)
            db.session.add(followeduser)
            db.session.commit()

            resp = c.post("/users/follow/2")

            # Check for redirect when adding follow
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, f'/users/{self.testuser.id}/following')
            
            resp = c.post("/users/stop-following/2")

            # Check for redirect when removing follow
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, f'/users/{self.testuser.id}/following')

            # Repeat process following the redirect
            resp = c.post("/users/follow/2", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Followed user should be present in page
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@followeduser', html)

            resp = c.post("/users/stop-following/2", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Followed user should no longer be present in page
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@followeduser', html)

            # Log out for remaining assertions
            c.get('/logout')

            add_resp = c.post("/users/follow/2")
            remove_resp = c.post("/users/stop-following/2")

            # Routes should redirect to root
            self.assertEqual(add_resp.status_code, 302)
            self.assertEqual(urlparse(add_resp.location).path, '/')
            self.assertEqual(remove_resp.status_code, 302)
            self.assertEqual(urlparse(remove_resp.location).path, '/')


    def test_update_profile_form(self):
        """Does the profile update form display properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get("users/profile")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Your Profile', html)

            # Log out for remaining assertions
            c.get('/logout')

            resp = c.get("/users/profile")

            # Routes should redirect to root
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/')


    def test_update_profile_submit(self):
        """Does the profile update form submit properly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post("users/profile", data={"username": "updateduser",
                                                    "email": "updated@email.com",
                                                    "password": "testuser"})

            # Check for redirect
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, f'/users/{self.testuser.id}')

            # Follow the redirect this time
            resp = c.post("users/profile", data={"username": "updateduser",
                                                    "email": "updated@email.com",
                                                    "password": "testuser"},
                                                    follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Check for updated data
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@updateduser', html)
            
            # Log out for remaining assertions
            c.get('/logout')

            resp = c.post("/users/profile")

            # Routes should redirect to root
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/')

    def test_delete_user(self):
        """Does the route work for deleting a user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            resp = c.post("/users/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/signup')

           # Log out for remaining assertions
            c.get('/logout')

            resp = c.post("/users/profile")

            # Routes should redirect to root
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/')