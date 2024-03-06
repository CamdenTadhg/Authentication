from unittest import TestCase
from app import app
from models import db, User, Feedback, bcrypt

app.config['TESTING'] = True

db.drop_all()
db.create_all()


# class FeedbackViewsTestCase(TestCase):
#     """Tests for app view functions"""

class UserModelTestCase(TestCase):
    """Tests for the methods on the User model"""

    def setUp(self):
        """Clean up any existing users"""

        User.query.delete()

        user = User.register(username="JaneDoe", password="secret", email="janedoe@gmail.com", first_name="Jane", last_name="Doe")
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

        self.assertIsInstance(User.authenticate('JaneDoe', 'secret'), User)

    def test_authenticate_incorrect(self):

        self.assertEqual(User.authenticate('JaneDoe', 'secret2'), False)