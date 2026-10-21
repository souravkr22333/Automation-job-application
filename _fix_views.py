import re

with open('Backend/django_app/applications/views.py', 'r') as f:
    content = f.read()

old = '''                        # Generate PDF and create TailoredResume (stored in 'Tailored resume' Supabase bucket)
                        try:
                            tailored_resume_obj = _create_tailored_resume_pdf(
                                user=request.user,
                                job=job,
                                original_resume=resume,
                                tailored_text=tailored_text,
                                changes=changes,
                                keywords_added=keywords_added
                            )
                            # Link queue item to the TailoredResume (FK now correctly points to TailoredResume)
                            queue_item.tailored_resume = tailored_resume_obj
                            queue_item.cover_letter = tailored_text

                        except Exception as pdf_err:
                            logger.warning(f"PDF generation failed (non-fatal): {str(pdf_err)}")

                        # Mark DONE so frontend poller does not revert to queued
                        queue_item.status = ApplicationQueue.Status.DONE
                        queue_item.save()

                        logger.info(f"Resume tailored for: {job.title} at {job.company}")

                        results.append({
                            'job_id': str(job.id),
                            'queue_item_id': str(queue_item.id),
                            'title': job.title,
                            'company': job.company,
                            'status': 'done',
                            'tailored': True,
                            'keywords_added': keywords_added,
                            'message': 'Resume tailored successfully'
                        })
                    else:
                        logger.error(f"Tailoring failed for {job.title}: {tailor_response.text}")
                        queue_item.status = ApplicationQueue.Status.FAILED
                        queue_item.error_message = f"Tailoring failed: {tailor_response.text}"
                        queue_item.save()

                        results.append({
                            'job_id': str(job.id),
                            'queue_item_id': str(queue_item.id),
                            'title': job.title,
                            'company': job.company,
                            'status': 'failed',
                            'tailored': False,
                            'message': 'Resume tailoring failed'
                        })

                except Exception as e:
                    logger.error(f"Tailoring error for {job.title}: {str(e)}")
                    queue_item.status = ApplicationQueue.Status.FAILED
                    queue_item.error_message = f"Tailoring error: {str(e)}"
                    queue_item.save()

                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(queue_item.id),
                        'title': job.title,
                        'company': job.company,
                        'status': 'failed',
                        'tailored': False,
                        'message': f'Resume tailoring failed: {str(e)}'
                    })'''

new = '''                        # Generate PDF and create TailoredResume (stored in 'Tailored resume' bucket)
                        tailored_resume_obj = None
                        try:
                            tailored_resume_obj = _create_tailored_resume_pdf(
                                user=request.user,
                                job=job,
                                original_resume=resume,
                                tailored_text=tailored_text,
                                changes=changes,
                                keywords_added=keywords_added
                            )
                        except Exception as pdf_err:
                            logger.warning(f"PDF generation/upload failed (non-fatal) for {job.title}: {str(pdf_err)}")

                        # Link queue item to TailoredResume if PDF was generated
                        if tailored_resume_obj:
                            queue_item.tailored_resume = tailored_resume_obj
                        queue_item.cover_letter = tailored_text

                        # Mark DONE - tailoring itself succeeded regardless of PDF generation
                        queue_item.status = ApplicationQueue.Status.DONE
                        queue_item.error_message = ''
                        queue_item.save()

                        logger.info(f"Resume tailored successfully: {job.title} at {job.company}")

                        results.append({
                            'job_id': str(job.id),
                            'queue_item_id': str(queue_item.id),
                            'title': job.title,
                            'company': job.company,
                            'status': 'done',
                            'tailored': True,
                            'keywords_added': keywords_added,
                            'message': 'Resume tailored successfully'
                        })
                    else:
                        error_detail = tailor_response.text[:500] if tailor_response.text else "Unknown error"
                        logger.error(f"Tailoring failed for {job.title}: {error_detail}")
                        queue_item.status = ApplicationQueue.Status.FAILED
                        queue_item.error_message = f"Tailoring failed: {error_detail}"
                        queue_item.save()

                        results.append({
                            'job_id': str(job.id),
                            'queue_item_id': str(queue_item.id),
                            'title': job.title,
                            'company': job.company,
                            'status': 'failed',
                            'tailored': False,
                            'message': 'Resume tailoring failed'
                        })

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Tailoring error for {job.title}: {error_msg}")
                    import traceback
                    logger.error(traceback.format_exc())
                    try:
                        queue_item.status = ApplicationQueue.Status.FAILED
                        queue_item.error_message = f"Tailoring error: {error_msg[:500]}"
                        queue_item.save()
                    except Exception:
                        logger.error(f"Failed to update queue item status for {job.id}")

                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(queue_item.id),
                        'title': job.title,
                        'company': job.company,
                        'status': 'failed',
                        'tailored': False,
                        'message': error_msg
                    })'''

count = content.count(old)
print(f'Found {count} occurrences of old string')
if count == 1:
    content = content.replace(old, new, 1)
    with open('Backend/django_app/applications/views.py', 'w') as f:
        f.write(content)
    print('Successfully replaced!')
elif count > 1:
    print(f'Multiple matches ({count}) found, need to be more specific')
elif 'tailored_resume_obj = None' in content:
    print('File already contains the fix!')
else:
    print('Pattern not found. Check if the file was already modified.')
    if 'Resume tailored successfully' in content:
        print('File already contains the updated success message - likely already fixed.')
    else:
        idx = content.find('def auto_generate')
        if idx > 0:
            print(content[idx:idx+2000])
