import unittest
from unittest.mock import Mock

from .services import ResumeStorageService


class ResumeStorageServiceTests(unittest.TestCase):
    def test_upload_bytes_uses_a_unique_storage_path_for_repeated_filenames(self):
        service = ResumeStorageService.__new__(ResumeStorageService)
        service.client = Mock()
        service.client.upload_file.side_effect = lambda **kwargs: {
            'public_url': f"https://storage.example.com/{kwargs['file_path']}",
            'path': kwargs['file_path'],
            'bucket': kwargs['bucket_name'],
        }

        first_upload = service.upload_bytes(
            bucket_name='Tailored resume',
            user_id='user-123',
            file_bytes=b'%PDF first',
            filename='Candidate_Engineer.pdf',
        )
        second_upload = service.upload_bytes(
            bucket_name='Tailored resume',
            user_id='user-123',
            file_bytes=b'%PDF second',
            filename='Candidate_Engineer.pdf',
        )

        self.assertNotEqual(first_upload['path'], second_upload['path'])
        self.assertTrue(first_upload['path'].startswith('users/user-123/'))
        self.assertEqual(first_upload['filename'], first_upload['path'].rsplit('/', 1)[-1])
