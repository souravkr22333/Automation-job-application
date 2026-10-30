import unittest
from unittest.mock import Mock

from .services import ResumeStorageService, build_tailored_resume_name


class ResumeStorageServiceTests(unittest.TestCase):
    def test_tailored_resume_name_respects_database_field_limit(self):
        long_resume_name = 'R' * 255
        long_company_name = 'C' * 300

        tailored_name = build_tailored_resume_name(long_resume_name, long_company_name)

        self.assertEqual(len(tailored_name), 255)
        self.assertTrue(tailored_name.endswith(long_company_name[-255:]))

    def test_tailored_resume_name_keeps_suffix_when_resume_name_is_long(self):
        tailored_name = build_tailored_resume_name('R' * 255, 'Sony')

        self.assertLessEqual(len(tailored_name), 255)
        self.assertTrue(tailored_name.endswith(' - Tailored for Sony'))

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
