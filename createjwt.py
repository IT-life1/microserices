import unittest
import jwt
# from  import CreateJWT  # Замените на имя вашего модуля

class TestCreateJWT(unittest.TestCase):
    def test_create_jwt(self):
        username = "test_user"
        secret = "supersecret"
        authz = True

        token = CreateJWT(username, secret, authz)
        decoded_token = jwt.decode(token, secret, algorithms=["HS256"])

        self.assertEqual(decoded_token["username"], username)
        self.assertEqual(decoded_token["admin"], "true")
        self.assertIn("exp", decoded_token)
        self.assertIn("iat", decoded_token)

    def test_create_jwt_with_false_authz(self):
        username = "test_user"
        secret = "supersecret"
        authz = False

        token = CreateJWT(username, secret, authz)
        decoded_token = jwt.decode(token, secret, algorithms=["HS256"])

        self.assertEqual(decoded_token["username"], username)
        self.assertEqual(decoded_token["admin"], "false")

if __name__ == "__main__":
    unittest.main()