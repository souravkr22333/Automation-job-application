import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from fastapi_app.app.routers import applications


class FakeStreamResponse:
    def raise_for_status(self):
        return None

    async def aiter_bytes(self, chunk_size):
        yield b'%PDF-test-resume'


class FakeStreamContext:
    async def __aenter__(self):
        return FakeStreamResponse()

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def stream(self, method, url):
        return FakeStreamContext()


class FakeSubmitter:
    def __init__(self, result):
        self.result = result
        self.resume_path = None

    async def submit_application(self, **kwargs):
        self.resume_path = kwargs['resume_path']
        with open(self.resume_path, 'rb') as resume_file:
            assert resume_file.read() == b'%PDF-test-resume'
        return self.result


class ApplicationSubmitEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.request = applications.SubmitApplicationRequest(
            queue_item_id='queue-id',
            user_data={'name': 'Test Candidate', 'email': 'candidate@example.com'},
            job={
                'id': 'job-id',
                'url': 'https://jobs.example.com/apply',
                'title': 'Engineer',
                'company': 'Example',
            },
            resume_url='https://storage.example.com/tailored.pdf',
            platform='linkedin',
        )

    async def test_rejects_invalid_internal_token(self):
        with patch.object(applications.settings, 'AUTO_APPLY_INTERNAL_TOKEN', 'configured-token'):
            with self.assertRaises(HTTPException) as error:
                await applications.submit_application(
                    self.request,
                    x_internal_token='incorrect-token',
                )

        self.assertEqual(error.exception.status_code, 401)

    async def test_downloads_tailored_pdf_and_returns_confirmed_success(self):
        submitter = FakeSubmitter({
            'status': 'success',
            'application_url': 'https://jobs.example.com/confirmation',
            'message': 'Submitted',
        })
        with patch.object(applications.settings, 'AUTO_APPLY_INTERNAL_TOKEN', 'configured-token'), \
                patch.object(applications.httpx, 'AsyncClient', return_value=FakeAsyncClient()), \
                patch.object(applications.SubmitFactory, 'get_submitter', return_value=submitter):
            result = await applications.submit_application(
                self.request,
                x_internal_token='configured-token',
            )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(
            result['application_url'],
            'https://jobs.example.com/confirmation',
        )
        self.assertFalse(os.path.exists(submitter.resume_path))

    async def test_pending_confirmation_is_not_reported_as_success(self):
        submitter = FakeSubmitter({
            'status': 'pending',
            'application_url': 'https://jobs.example.com/apply',
            'message': 'Could not verify confirmation',
        })
        with patch.object(applications.settings, 'AUTO_APPLY_INTERNAL_TOKEN', 'configured-token'), \
                patch.object(applications.httpx, 'AsyncClient', return_value=FakeAsyncClient()), \
                patch.object(applications.SubmitFactory, 'get_submitter', return_value=submitter):
            result = await applications.submit_application(
                self.request,
                x_internal_token='configured-token',
            )

        self.assertEqual(result['status'], 'pending_confirmation')
        self.assertFalse(os.path.exists(submitter.resume_path))
