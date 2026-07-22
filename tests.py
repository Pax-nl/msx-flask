import io
import json
import unittest
import os
from utils import safe_relative_path, safe_path, SERVE_DIRECTORY
from translations import TRANSLATIONS
from app import app

class TestMSXServer(unittest.TestCase):
    def test_safe_relative_path(self):
        # Good paths
        self.assertEqual(safe_relative_path("test/file.txt"), "test/file.txt")
        self.assertEqual(safe_relative_path(""), "")
        
        # Dangerous paths should raise ValueError
        with self.assertRaises(ValueError):
            safe_relative_path("../outside.txt")
        with self.assertRaises(ValueError):
            safe_relative_path("/absolute/path")

    def test_safe_path(self):
        # Should stay within SERVE_DIRECTORY
        path = safe_path("subdir/game.rom")
        self.assertTrue(path.startswith(os.path.abspath(SERVE_DIRECTORY)))

    def test_translations(self):
        # Verify both languages exist and have same keys
        self.assertIn("nl", TRANSLATIONS)
        self.assertIn("en", TRANSLATIONS)
        nl_keys = set(TRANSLATIONS["nl"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        self.assertEqual(nl_keys, en_keys, "NL and EN translation keys must match!")

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        os.makedirs(SERVE_DIRECTORY, exist_ok=True)

    def test_api_upload_download_delete_flow(self):
        # 1. Test File Upload via API
        test_filename = "test_api_file.rom"
        test_content = b"MSX_TEST_DATA_12345"
        
        data = {
            'file': (io.BytesIO(test_content), test_filename),
            'target_dir': ''
        }
        res = self.client.post('/api/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 201)
        res_json = res.get_json()
        self.assertTrue(res_json['success'])
        self.assertEqual(res_json['filename'], test_filename)
        
        uploaded_path = os.path.join(SERVE_DIRECTORY, test_filename)
        self.assertTrue(os.path.exists(uploaded_path))

        # 2. Test File List API
        res = self.client.get('/api/files')
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertTrue(res_json['success'])
        file_names = [f['name'] for f in res_json['files']]
        self.assertIn(test_filename, file_names)

        # 3. Test File Download via Path
        res = self.client.get(f'/api/download/{test_filename}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, test_content)
        res.close()

        # Test File Download via Query Param
        res = self.client.get(f'/api/download?path={test_filename}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, test_content)
        res.close()

        # 4. Test File Delete via API (POST JSON)
        res = self.client.post('/api/delete', json={'path': test_filename})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        self.assertFalse(os.path.exists(uploaded_path))

    def test_api_delete_via_http_delete_method(self):
        # Create dummy file to delete
        dummy_file = os.path.join(SERVE_DIRECTORY, "to_delete.txt")
        with open(dummy_file, "w") as f:
            f.write("delete me")
        
        res = self.client.delete('/api/delete?path=to_delete.txt')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        self.assertFalse(os.path.exists(dummy_file))

    def test_api_error_handling(self):
        # Download non-existent file
        res = self.client.get('/api/download/non_existent_file.rom')
        self.assertEqual(res.status_code, 404)
        self.assertFalse(res.get_json()['success'])

        # Delete non-existent file
        res = self.client.post('/api/delete', json={'path': 'non_existent.rom'})
        self.assertEqual(res.status_code, 404)

        # Invalid path traversal attempt
        res = self.client.post('/api/delete', json={'path': '../outside.txt'})
        self.assertEqual(res.status_code, 400)

if __name__ == "__main__":
    unittest.main()
