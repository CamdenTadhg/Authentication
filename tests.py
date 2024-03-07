from unittest import TestCase
from app import app
from models import db, User, Feedback, bcrypt
from flask import session

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()

class FeedbackViewsTestCase(TestCase):
    """Tests for app view functions"""

    def setUp(self):
        """Add sample users and feedback"""

        Feedback.query.delete()
        User.query.delete()

        user1 = User.register(username="JaneDoe", pwd="secretsecret!", email="janedoe@gmail.com", first_name = "Jane", last_name="Doe")
        db.session.add(user1)
        user2 = User.register(username="JohnDoe", pwd="secret2secret2!", email="johndoe@gmail.com", first_name="John", last_name="Doe")
        db.session.add(user2)
        user3 = User.register(username="DianaBright", pwd="passwordpassword!", email="dianabright@gmail.com", first_name="Diana", last_name="Bright")
        db.session.add(user3)
        db.session.commit()
        stmt = update(User).where(User.username == "JohnDoe").values(is_admin=True)
        db.session.execute(stmt)
        db.session.commit()
        

        feedback1 = Feedback(title="testing 1", content="This is the first test feedback", username= 'JaneDoe')
        feedback2 = Feedback(title="testing 2", content="This is the second test feedback", username='JohnDoe')
        db.session.add(feedback1)
        db.session.add(feedback2)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transactions and clear session"""
        with app.test_client() as client: 
            with client.session_transaction() as change_session:
                if change_session.get('username'):
                    change_session.pop('username')
                if change_session.get('admin'):
                    change_session.pop('admin')
        db.session.rollback()
    
    def test_display_home_unlogged(self):
        with app.test_client() as client:
            resp = client.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Please login', html)
            self.assertIn('Register', html)
    
    def test_display_home_loggedin(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = "JaneDoe"
            resp = client.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('Please login', html)
            self.assertIn('My Account', html)
    
    def test_register_user_get(self):
        with app.test_client() as client:
            resp = client.get('/register')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Registration Form', html)

    def test_register_user_post(self):
        with app.test_client() as client:
            resp = client.post('/register', data = {"username": "Superman", "password": "supermansuperman!", "password2": "supermansuperman!", "email": "superman@gmail.com", "first_name": "Super", "last_name": "Man"} )

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'/user/Superman')
            self.assertEqual(session['username'], 'Superman')

    
    def test_register_user_post_redirect(self):
        with app.test_client() as client:
            resp = client.post('/register', data = {"username": "Superman", "password": "supermansuperman!", "password2": "supermansuperman!", "email": "superman@gmail.com", "first_name": "Super", "last_name": "Man"}, follow_redirects=True ) 
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Superman', html)
            self.assertEqual(session['username'], 'Superman')

    def test_register_user_loggedin(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = "JaneDoe"
            resp = client.get('/register')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/')

    def test_register_user_loggedin_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.get('/register', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('My Account', html)

    def test_register_user_duplicate_username(self):
        with app.test_client() as client:
            resp = client.post('/register', data= {"username": "JaneDoe", "password": "passwordpassword!", "password2": "passwordpassword!", "email": "janedoe2@gmail.com", "first_name": "Jane", "last_name": "Doe"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username taken', html)
    
    def test_register_user_password_unmatch(self):
        with app.test_client() as client:
            resp = client.post('/register', data={"username": "Superman", "password": "supermansuperman!", "password2": "superman2superman2!", "email": "superman@gmail.com", "first_name": "Super", "last_name": "Man"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Passwords do not match', html)

    def test_register_user_password_too_short(self):
        with app.test_client() as client:
            resp = client.post('/register', data={"username": "Superman", "password": "superman!", "password2": "superman!", "email": "superman@gmail.com", "first_name": "Super", "last_name": "Man"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Password must be at least 10 characters', html)

    def test_register_user_password_too_simple(self):
        with app.test_client() as client:
            resp = client.post('/register', data={"username": "Superman", "password": "supermansuperman", "password2": "supermansuperman", "email": "superman@gmail.com", "first_name": "Super", "last_name": "Man"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Password must contain at least one special character', html)
    
    def test_login_user_get(self): 
        with app.test_client() as client:
            resp = client.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Login Form', html)

    def test_login_user_loggedin(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = "JaneDoe"
            resp = client.get('/login')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/')

    def test_login_use_loggedin_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.get('/login', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('already logged in', html)

    def test_login_user_correct(self):
        with app.test_client() as client:
            resp = client.post('/login', data={"username": "JaneDoe", "password": "secretsecret!"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'/user/JaneDoe')
            self.assertEqual(session['username'], 'JaneDoe')
            self.assertEqual(session.get('admin'), False)
    
    def test_login_user_correct_redirect(self):
        with app.test_client() as client:
            resp = client.post('/login', data={"username": "JaneDoe", "password": "secretsecret!"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('janedoe@gmail.com', html)
            self.assertEqual(session['username'], 'JaneDoe')

    def test_login_admin_user_correct(self):
        with app.test_client() as client:
            resp = client.post('/login', data={"username": "JohnDoe", "password": "secret2secret2!"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JohnDoe')
            self.assertEqual(session['username'], 'JohnDoe')
            self.assertEqual(session['admin'], True)

    def test_login_admin_user_correct_redirect(self):
        with app.test_client() as client:
            resp = client.post('/login', data={"username": "JohnDoe", "password": "secret2secret2!"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('johndoe@gmail.com', html)
            self.assertEqual(session['username'], 'JohnDoe')
            self.assertEqual(session['admin'], True)

    def test_login_user_incorrect_username(self): 
        with app.test_client() as client:
            resp = client.post('/login', data={"username": "JaneCDoe", "password": "passwordpassword!"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("invalid username", html)
            self.assertFalse(session.get('username'))
    
    def test_login_user_incorrect_password(self):
        with app.test_client() as client:
            resp = client.post('/login', data={"username": "JaneDoe", "password": "passwordpassword"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("invalid password", html)
            self.assertFalse(session.get('username'))

    def test_logout(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp2 = client.post('/logout')

            self.assertEqual(resp2.status_code, 302)
            self.assertEqual(resp2.location, '/')
            self.assertFalse(session.get('username'))
    
    def test_logout_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp2 = client.post('/logout', follow_redirects=True)
            html = resp2.get_data(as_text=True)

            self.assertEqual(resp2.status_code, 200)
            self.assertIn('Login', html)
            self.assertFalse(session.get('username'))     
    
    def test_logout_admin(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
            resp2 = client.post('/logout')

            self.assertEqual(resp2.status_code, 302)
            self.assertEqual(resp2.location, '/')
            self.assertFalse(session.get('username')) 
            self.assertFalse(session.get('admin')) 

    def test_logout_admin_redirect(self):      
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
            resp2 = client.post('/logout', follow_redirects=True)
            html = resp2.get_data(as_text=True)

            self.assertEqual(resp2.status_code, 200)
            self.assertIn('Login', html)
            self.assertFalse(session.get('username')) 
            self.assertFalse(session.get('admin')) 

    def test_display_user_loggedout(self):
        with app.test_client() as client:
            resp = client.get('/user/JaneDoe')
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)

    def test_display_user_no_user(self):
        with app.test_client() as client:
            resp = client.get('/user/camdentadhg')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)

    def test_display_user_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.get('/user/JaneDoe')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Delete Account', html)
            self.assertIn('fa-trash', html)
            self.assertIn('testing 1', html)
            

    def test_display_user_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'DianaBright'
            resp = client.get('/user/JaneDoe')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing 1', html)
            self.assertNotIn('Delete Account', html)
            self.assertNotIn('fa-trash', html)

    def test_display_user_admin_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            resp = client.get('/user/JaneDoe')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Delete Account', html)
            self.assertIn('fa-trash', html)
            self.assertIn('testing 1', html)
    
    def test_delete_user_loggedout(self):
        with app.test_client() as client:
            resp = client.post('/user/JaneDoe/delete')
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)

    def test_delete_user_nouser(self):
        with app.test_client() as client:
            resp = client.post('/user/camdentadhg/delete')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)

    def test_delete_user_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.post('/user/JaneDoe/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/')
            self.assertFalse(session.get('username')) 
            self.assertFalse(session.get('admin')) 

    def test_delete_user_right_user_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.post('/user/JaneDoe/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Register', html)
            self.assertIn('Account deleted', html)
            self.assertFalse(session.get('username')) 
            self.assertFalse(session.get('admin'))

    def test_delete_user_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'DianaBright'          
            resp = client.post('/user/JaneDoe/delete')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You do not have permissions', html)
            self.assertEqual(session['username'], 'DianaBright') 

    def test_delete_user_admin(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            resp = client.post('/user/JaneDoe/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/')
            self.assertEqual(session['username'], 'JohnDoe')
            self.assertEqual(session['admin'], True)

    def test_delete_user_admin_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            resp = client.post('/user/JaneDoe/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Logout', html)
            self.assertIn('Account deleted', html)
            self.assertEqual(session['username'], 'JohnDoe')
            self.assertEqual(session['admin'], True)

    def test_add_feedback_loggedout_get(self):
        with app.test_client() as client:
            resp = client.get('/user/JaneDoe/feedback/add')
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)

    def test_add_feedback_loggedout_post(self):
        with app.test_client() as client:
            resp = client.post('/user/JaneDoe/feedback/add', data={'title': 'testing 3', 'content': 'This is the third test feedback'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)
        
    def test_add_feedback_nouser_get(self):
        with app.test_client() as client:
            resp = client.get('/user/camdentadhg/feedback/add')
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)
    
    def test_add_feedback_nouser_post(self):
        with app.test_client() as client:
            resp = client.post('/user/camdentadhg/feedback/add', data={'title': 'testing 3', 'content': 'This is the third test feedback'})
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)

    def test_add_feedback_get_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session: 
                change_session['username'] = 'JaneDoe'
            resp = client.get('/user/JaneDoe/feedback/add')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Add Your Feedback', html)
    
    def test_add_feedback_get_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session: 
                change_session['username'] = 'DianaBright'
            resp = client.get('/user/JaneDoe/feedback/add')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You do not have permissions', html)

    def test_add_feedback_get_admin_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session: 
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            resp = client.get('/user/JaneDoe/feedback/add')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Add Your Feedback', html)

    def test_add_feedback_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.post('/user/JaneDoe/feedback/add', data = {'title': 'testing 3', 'content': 'This is the third test feedback'})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JaneDoe')

    def test_add_feedback_right_user_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            resp = client.post('/user/JaneDoe/feedback/add', data = {'title': 'testing 3', 'content': 'This is the third test feedback'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing 3', html)
    
    def test_add_feedback_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'DianaBright'
            resp = client.post('/user/JaneDoe/feedback/add', data = {'title': 'testing 3', 'content': 'This is the third test feedback'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)

    def test_add_feedback_admin_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            resp = client.post('/user/JaneDoe/feedback/add', data = {'title': 'testing 3', 'content': 'This is the third test feedback'})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JaneDoe')

    def test_add_feedback_admin_user_redirect(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            resp = client.post('/user/JaneDoe/feedback/add', data = {'title': 'testing 3', 'content': 'This is the third test feedback'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing 3', html)
    
    def test_update_feedback_loggedout_get(self):
        with app.test_client() as client:
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.get(f'/feedback/{test_feedback.id}/update')
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)
    
    def test_update_feedback_loggedout_post(self):
        with app.test_client() as client:
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/update', data={'title': 'testing update', 'content': 'This is the first test feedback'})
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)
    
    def test_update_feedback_nofeedback_get(self):
        with app.test_client() as client:
            resp = client.get('/feedback/10000/update')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)
    
    def test_update_feedback_nofeedback_post(self):
        with app.test_client() as client:
            resp = client.post('/feedback/10000/update', data={'title': 'testing 4', 'content': 'This is the fourth test feedback'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)

    def test_update_feedback_get_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.get(f'/feedback/{test_feedback.id}/update')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing 1', html)
    
    def test_update_feedback_get_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'DianaBright'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.get(f'/feedback/{test_feedback.id}/update')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You do not have permissions', html)

    def test_update_feedback_get_admin_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.get(f'/feedback/{test_feedback.id}/update')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing 1', html)

    def test_update_feedback_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/update', data={'title': 'testing update', 'content': 'This is the first test feedback'})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JaneDoe')

    def test_update_feedback_right_user_redirect(self):
       with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/update', data={'title': 'testing update', 'content': 'This is the first test feedback'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing update', html)

    def test_update_feedback_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'DianaBright'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/update', data={'title': 'testing update', 'content': 'This is the first test feedback'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You do not have permissions', html)

    def test_update_feedback_admin_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/update', data={'title': 'testing update', 'content': 'This is the first test feedback'})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JaneDoe')

    def test_update_feedback_admin_user_redirect(self):
       with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/update', data={'title': 'testing update', 'content': 'This is the first test feedback'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing update', html)

    def test_delete_feedback_loggedout(self):
        with app.test_client() as client:
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/delete')
            html  = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You must be logged in', html)

    def test_delete_feedback_nofeedback(self):
        with app.test_client() as client:
            resp = client.post('/feedback/10000/delete')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("We're sorry", html)

    def test_delete_feedback_right_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JaneDoe')

    def test_delete_feedback_right_user_redirect(self):
       with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JaneDoe'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('testing 1', html)

    def test_delete_feedback_wrong_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'DianaBright'
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/delete')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You do not have permissions', html)

    def test_delete_feedback_admin_user(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/user/JaneDoe')

    def test_delete_feedback_admin_user_redirect(self):
       with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['username'] = 'JohnDoe'
                change_session['admin'] = True
            test_feedback = db.session.execute(db.select(Feedback).where(Feedback.title == "testing 1")).scalar()
            resp = client.post(f'/feedback/{test_feedback.id}/delete',  follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('testing 1', html)


class UserModelTestCase(TestCase):
    """Tests for the methods on the User model"""

    def setUp(self):
        """Clean up any existing users"""

        Feedback.query.delete()
        User.query.delete()

        user = User.register(username="JaneDoe", pwd="secret", email="janedoe@gmail.com", first_name="Jane", last_name="Doe")
        db.session.add(user)
        db.session.commit()


    def tearDown(self):
        """Clean up any fouled transactions"""

        db.session.rollback()
    
    def test_full_name(self):
        user = User.query.get('JaneDoe')

        self.assertEqual(user.fullname, "Jane Doe")

    def test_register(self):
        user = User.query.get('JaneDoe')

        self.assertIsInstance(user, User)
        self.assertNotEqual(user.password, 'secret')
        self.assertEqual(user.first_name, 'Jane')
    
    def test_authenticate_correct(self):
        user = User.authenticate('JaneDoe', 'secret')

        self.assertIsInstance(user, User)
        self.assertEqual(user.first_name, 'Jane')

    def test_authenticate_incorrect(self):

        self.assertEqual(User.authenticate('JaneDoe', 'secret2'), False)