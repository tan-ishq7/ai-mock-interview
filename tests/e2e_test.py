"""
End-to-end test for the AI Mock Interview Agent.

Uses Playwright for browser automation + screenshots.
Install: pip install playwright && playwright install chromium

Usage:
    python tests/e2e_test.py

Screenshots saved to: tests/screenshots/
"""

import asyncio
import os
import sys
import time
import httpx
from pathlib import Path

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
SAMPLE_PDF = Path(__file__).parent.parent / "tests" / "sample_resume.pdf"


def ensure_dirs():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


async def test_backend_health():
    """Test 1: Backend health check."""
    print("\n[Test 1] Backend health check...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print(f"  PASS - {data}")
    return True


async def test_resume_upload(pdf_path: str = None):
    """Test 2: Resume upload and parsing."""
    print("\n[Test 2] Resume upload and parsing...")
    pdf_file = pdf_path or str(SAMPLE_PDF)

    if not os.path.exists(pdf_file):
        print(f"  SKIP - No sample PDF at {pdf_file}")
        return None

    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(pdf_file, "rb") as f:
            resp = await client.post(
                f"{BACKEND_URL}/api/resume/upload",
                files={"file": ("resume.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "data" in data
        print(f"  PASS - Parsed {len(data['data'])} sections")
        return data["data"]


async def test_interview_flow(candidate_id: str = None):
    """Test 3: Start interview and send messages."""
    print("\n[Test 3] Interview flow...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Start interview
        resp = await client.post(
            f"{BACKEND_URL}/api/interview/start",
            json={"candidate_id": candidate_id or "test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  Start: {data}")

        session_id = data.get("session_id", "test")

        # Send a candidate response
        resp = await client.post(
            f"{BACKEND_URL}/api/interview/{session_id}/respond",
            json={
                "message": "I am a machine learning scientist with 5 years of experience at Amazon Alexa, working on NLP and TTS systems."
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  Respond: {data}")

        # Check session status
        resp = await client.get(f"{BACKEND_URL}/api/interview/{session_id}/status")
        assert resp.status_code == 200
        print(f"  Status: {resp.json()}")

    return True


async def test_voice_endpoints():
    """Test 4: Voice transcription and synthesis."""
    print("\n[Test 4] Voice endpoints...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test TTS
        resp = await client.post(
            f"{BACKEND_URL}/api/voice/synthesize",
            json={"text": "Could you please tell me about yourself?"},
        )
        print(f"  TTS status: {resp.status_code}")

    return True


async def test_evaluation_endpoint():
    """Test 5: Evaluation and report."""
    print("\n[Test 5] Evaluation endpoint...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BACKEND_URL}/api/evaluation/report/test-session")
        print(f"  Report status: {resp.status_code}")

    return True


async def test_browser_e2e():
    """Test 6: Full browser E2E with Playwright screenshots."""
    print("\n[Test 6] Browser E2E with screenshots...")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  SKIP - Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        # Screenshot 1: Landing / Upload page
        print("  Loading upload page...")
        await page.goto(FRONTEND_URL)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_upload_page.png"))
        print(f"  Screenshot: 01_upload_page.png")

        # Screenshot 2: Try uploading a PDF (if available)
        upload_input = page.locator('input[type="file"]')
        if await upload_input.count() > 0 and SAMPLE_PDF.exists():
            await upload_input.set_input_files(str(SAMPLE_PDF))
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "02_pdf_uploaded.png"))
            print(f"  Screenshot: 02_pdf_uploaded.png")

            # Click start interview button if visible
            start_btn = page.locator('button:has-text("Start Interview")')
            if await start_btn.count() > 0:
                await start_btn.click()
                await page.wait_for_timeout(3000)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "03_interview_started.png"))
                print(f"  Screenshot: 03_interview_started.png")

        # Screenshot 3: Interview page (navigate directly)
        await page.goto(f"{FRONTEND_URL}/interview/test-session")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "04_interview_page.png"))
        print(f"  Screenshot: 04_interview_page.png")

        # Screenshot 4: Report page
        await page.goto(f"{FRONTEND_URL}/report/test-session")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "05_report_page.png"))
        print(f"  Screenshot: 05_report_page.png")

        await browser.close()
        print("  PASS - All screenshots captured")

    return True


async def run_all_tests(pdf_path: str = None):
    """Run all e2e tests in sequence."""
    ensure_dirs()
    print("=" * 60)
    print("AI Mock Interview Agent - E2E Test Suite")
    print("=" * 60)

    results = {}

    # API tests
    try:
        results["health"] = await test_backend_health()
    except Exception as e:
        print(f"  FAIL - {e}")
        results["health"] = False

    try:
        results["resume_upload"] = await test_resume_upload(pdf_path)
    except Exception as e:
        print(f"  FAIL - {e}")
        results["resume_upload"] = False

    try:
        results["interview_flow"] = await test_interview_flow()
    except Exception as e:
        print(f"  FAIL - {e}")
        results["interview_flow"] = False

    try:
        results["voice"] = await test_voice_endpoints()
    except Exception as e:
        print(f"  FAIL - {e}")
        results["voice"] = False

    try:
        results["evaluation"] = await test_evaluation_endpoint()
    except Exception as e:
        print(f"  FAIL - {e}")
        results["evaluation"] = False

    # Browser test
    try:
        results["browser_e2e"] = await test_browser_e2e()
    except Exception as e:
        print(f"  FAIL - {e}")
        results["browser_e2e"] = False

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASS" if passed else ("SKIP" if passed is None else "FAIL")
        print(f"  [{status}] {test_name}")

    screenshots = list(SCREENSHOTS_DIR.glob("*.png"))
    if screenshots:
        print(f"\nScreenshots saved to: {SCREENSHOTS_DIR}")
        for s in sorted(screenshots):
            print(f"  - {s.name}")

    return results


if __name__ == "__main__":
    pdf_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_all_tests(pdf_arg))
