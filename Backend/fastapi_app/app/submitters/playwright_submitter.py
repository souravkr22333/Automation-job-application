# backend/fastapi_app/submitters/playwright_submitter.py (complete with error handling)
import asyncio
import logging
import os
import time
import tempfile

from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

from ..config import settings

logger = logging.getLogger(__name__)


class ApplicationSubmitter:
    """Playwright-based application submitter with comprehensive error handling"""
    
    def __init__(self, headless: Optional[bool] = None):
        self.headless = settings.PLAYWRIGHT_HEADLESS if headless is None else headless
        self.max_retries = 3
        self.retry_delay = 2
    
    async def submit_application(
        self,
        user_data: Dict[str, Any],
        job: Dict[str, Any],
        resume_path: str,
        cover_letter: str,
        platform: str = "linkedin"
    ) -> Dict[str, Any]:
        """Submit an application using Playwright with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                result = await self._submit_application_internal(
                    user_data, job, resume_path, cover_letter, platform
                )
                if result.get("status") in ("success", "pending"):
                    return result
                if attempt < self.max_retries - 1:
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries} for {job.get('title')}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return result
            except Exception as e:
                logger.error(f"Submission attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    return {"status": "failed", "reason": str(e), "attempts": attempt + 1}
        
        return {"status": "failed", "reason": "Max retries exceeded"}
    
    async def _submit_application_internal(
        self,
        user_data: Dict[str, Any],
        job: Dict[str, Any],
        resume_path: str,
        cover_letter: str,
        platform: str
    ) -> Dict[str, Any]:
        """Internal submission logic"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
            page = await context.new_page()
            
            try:
                # Navigate to job page with timeout
                await page.goto(job['url'], wait_until="networkidle", timeout=30000)
                
                # Handle login redirects
                if "linkedin.com/login" in page.url:
                    logger.info("Redirected to LinkedIn login - skipping")
                    return {"status": "failed", "reason": "Login required"}
                
                # Wait for page to load
                await page.wait_for_load_state("networkidle")
                
                # Find and click apply button
                apply_found = await self._find_and_click_apply(page)
                if not apply_found:
                    logger.warning(f"Apply button not found for {job.get('title')}")
                    return {"status": "failed", "reason": "Apply button not found"}
                
                # Wait for application form
                try:
                    await page.wait_for_selector("form, .application-form, [role='dialog']", timeout=10000)
                except PlaywrightTimeoutError:
                    logger.warning("No form found after clicking apply")
                
                # Fill form fields
                await self._fill_application_form(page, user_data, cover_letter)
                
                # Upload resume
                await self._upload_resume(page, resume_path)
                
                # Handle multi-step forms
                await self._handle_multi_step_form(page)
                
                # Submit form
                submitted = await self._submit_form(page)
                if not submitted:
                    return {"status": "failed", "reason": "Form submission failed"}
                
                # Wait for confirmation
                confirmation = await self._wait_for_confirmation(page)
                
                # Take screenshot for debugging
                if not confirmation:
                    screenshot_path = os.path.join(
                        tempfile.gettempdir(),
                        f"submission_{job.get('id', 'unknown')}_{int(time.time())}.png",
                    )
                    try:
                        await page.screenshot(path=screenshot_path)
                        logger.info(f"Screenshot saved to {screenshot_path}")
                    except Exception:
                        logger.exception("Failed to save submission screenshot")
                        screenshot_path = None
                else:
                    screenshot_path = None
                
                return {
                    "status": "success" if confirmation else "pending",
                    "application_url": page.url,
                    "message": "Application submitted successfully" if confirmation else "Application pending confirmation",
                    "screenshot": screenshot_path if not confirmation else None
                }
                
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout error: {str(e)}")
                return {"status": "failed", "reason": f"Timeout: {str(e)}"}
            except Exception as e:
                logger.error(f"Submission error: {str(e)}")
                return {"status": "failed", "reason": str(e)}
            finally:
                await browser.close()
    
    async def _find_and_click_apply(self, page: Page) -> bool:
        """Find and click the apply button with multiple strategies"""
        apply_selectors = [
            "button:has-text('Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Submit Application')",
            "button:has-text('Easy Apply')",
            "button:has-text('Apply on company site')",
            ".apply-button",
            ".job-apply-button",
            "[data-testid='apply-button']",
            "a:has-text('Apply')",
            "button[aria-label*='Apply']",
            ".jobs-apply-button"
        ]
        
        for selector in apply_selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=2000):
                    await button.click()
                    await asyncio.sleep(1.5)  # Wait for any animations
                    return True
            except Exception:
                continue
        
        return False
    
    async def _fill_application_form(self, page: Page, user_data: Dict[str, Any], cover_letter: str):
        """Fill the application form fields"""
        # Common field mappings with variations
        field_mappings = {
            "name": ["name", "full_name", "candidate_name", "applicant_name"],
            "first_name": ["first_name", "firstName", "fname", "first-name"],
            "last_name": ["last_name", "lastName", "lname", "last-name"],
            "email": ["email", "email_address", "emailAddress", "e-mail"],
            "phone": ["phone", "phone_number", "phoneNumber", "mobile", "telephone"],
            "cover_letter": ["cover_letter", "coverLetter", "message", "additional_information"],
            "resume": ["resume", "cv", "attachment", "file"],
        }
        
        # Fill standard fields
        for field_type, selectors in field_mappings.items():
            if field_type == "cover_letter" and cover_letter:
                value = cover_letter
            elif field_type in user_data:
                value = user_data[field_type]
            else:
                continue
            
            await self._fill_field_with_selectors(page, selectors, value)
        
        # Handle name splitting
        if "name" in user_data and " " in user_data["name"]:
            first_name, last_name = user_data["name"].split(" ", 1)
            await self._fill_field_with_selectors(page, field_mappings["first_name"], first_name)
            await self._fill_field_with_selectors(page, field_mappings["last_name"], last_name)
    
    async def _fill_field_with_selectors(self, page: Page, selectors: List[str], value: str):
        """Fill a field using multiple selector strategies"""
        for selector in selectors:
            # Try different input types
            input_selectors = [
                f"input[name='{selector}']",
                f"input[id='{selector}']",
                f"input[placeholder*='{selector}' i]",
                f"input[aria-label*='{selector}' i]",
                f"textarea[name='{selector}']",
                f"textarea[id='{selector}']",
                f"textarea[placeholder*='{selector}' i]",
                f"[data-testid='{selector}']",
                f"[data-field='{selector}']",
                f"input[data-testid='{selector}']"
            ]
            
            for input_selector in input_selectors:
                try:
                    element = page.locator(input_selector).first
                    if await element.is_visible(timeout=1000):
                        await element.fill(str(value))
                        await asyncio.sleep(0.3)
                        return True
                except Exception:
                    continue
        
        return False
    
    async def _upload_resume(self, page: Page, resume_path: str) -> bool:
        """Upload resume file"""
        upload_selectors = [
            "input[type='file']",
            "input[accept*='pdf']",
            "input[accept*='doc']",
            "[data-testid='resume-upload']",
            ".resume-upload input[type='file']",
            "#resume-upload"
        ]
        
        for selector in upload_selectors:
            try:
                resume_input = page.locator(selector).first
                if await resume_input.is_visible(timeout=1000):
                    await resume_input.set_input_files(resume_path)
                    await asyncio.sleep(1)
                    logger.info("Resume uploaded successfully")
                    return True
            except Exception:
                continue
        
        logger.warning("Resume upload input not found")
        return False
    
    async def _handle_multi_step_form(self, page: Page):
        """Handle multi-step forms (Next buttons)"""
        max_steps = 5
        for step in range(max_steps):
            try:
                next_buttons = [
                    "button:has-text('Next')",
                    "button:has-text('Continue')",
                    "button[type='button']:has-text('Next')",
                    ".next-button",
                    "[data-testid='next-button']"
                ]
                
                found_next = False
                for selector in next_buttons:
                    try:
                        button = page.locator(selector).first
                        if await button.is_visible(timeout=1000):
                            await button.click()
                            await asyncio.sleep(1)
                            found_next = True
                            break
                    except Exception:
                        continue
                
                if not found_next:
                    break
                    
            except Exception:
                break
    
    async def _submit_form(self, page: Page) -> bool:
        """Submit the application form"""
        submit_selectors = [
            "button[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Submit Application')",
            "button:has-text('Apply')",
            "button:has-text('Send Application')",
            "button:has-text('Complete Application')",
            ".submit-button",
            "[data-testid='submit-button']",
            "button[aria-label*='Submit']"
        ]
        
        for selector in submit_selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=1000):
                    await button.click()
                    await asyncio.sleep(2)
                    return True
            except Exception:
                continue
        
        return False
    
    async def _wait_for_confirmation(self, page: Page) -> bool:
        """Wait for confirmation message"""
        confirmation_selectors = [
            "text=Application submitted",
            "text=Application received",
            "text=Thank you for applying",
            "text=Success",
            "text=Your application has been sent",
            "text=Application sent",
            "[data-testid='confirmation']",
            ".confirmation-message",
            ".success-message",
            ".thank-you"
        ]
        
        for selector in confirmation_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                return True
            except Exception:
                continue
        
        # Check for URL change indicating success
        current_url = page.url
        if "thank-you" in current_url.lower() or "success" in current_url.lower():
            return True
        
        return False