import os

import pytest
from playwright.sync_api import Page, expect


BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_IPC47_E2E") != "1",
    reason="Set RUN_IPC47_E2E=1 to run this data-changing browser test",
)


def _required_setting(name):
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Set {name} to run the IPC-47 browser test")
    return value


def _login(page: Page, username: str, password: str):
    page.goto(f"{BASE_URL}/accounts/login/")
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.locator('button[type="submit"]').click()


def test_ipc47_operator_row_reaches_qa(page: Page):
    """Verify an IPC-47 row survives redirect and appears in QA's queue."""
    phase_id = _required_setting("IPC47_PHASE_EXECUTION_ID")
    batch_number = _required_setting("IPC47_BATCH_NUMBER")
    operator_username = _required_setting("IPC47_OPERATOR_USERNAME")
    operator_password = _required_setting("IPC47_OPERATOR_PASSWORD")
    qa_username = _required_setting("IPC47_QA_USERNAME")
    qa_password = _required_setting("IPC47_QA_PASSWORD")

    row_marker = "Playwright IPC47 persistence check"

    _login(page, operator_username, operator_password)
    page.goto(f"{BASE_URL}/dashboards/bmr-forms/view/{phase_id}/")
    expect(page.locator("body")).to_contain_text("IPC Page 47")

    page.locator('input[name="ipc47_row_date"]').fill("2026-09-21")
    page.locator('input[name="ipc47_row_appear"]').fill(row_marker)
    page.locator('input[name="ipc47_row_printed"]').fill("Correct")
    page.locator('select[name="ipc47_row_passfail"]').select_option(label="PASS")
    page.locator('input[name="ipc47_row_doneby"]').fill(operator_username)
    page.locator('button[value="ipc_row_add_47"]').click()

    expect(page.locator("body")).to_contain_text(row_marker)

    qa_page = page.context.new_page()
    try:
        _login(qa_page, qa_username, qa_password)
        qa_page.goto(f"{BASE_URL}/dashboards/qa/")
        expect(qa_page.locator("body")).to_contain_text("Your turn to add row")
        expect(qa_page.locator("body")).to_contain_text(batch_number)
    finally:
        qa_page.close()
