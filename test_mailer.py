"""
Offline sanity check for mailer.send_email. Mocks smtplib.SMTP_SSL so
this runs with no real network call and no real Gmail account --
verifies our code calls login/sendmail correctly, not that Gmail
actually accepts it.
"""

import os
from unittest.mock import patch, MagicMock

os.environ["EMAIL_FROM"] = "kate@example.com"
os.environ["EMAIL_APP_PASSWORD"] = "fake_app_password"
os.environ["EMAIL_TO"] = "kate@example.com"

from news_agent.mailer import send_email

with patch("smtplib.SMTP_SSL") as mock_smtp_cls:
    mock_server = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_server

    send_email("<html><body>test report</body></html>", subject="Test Briefing")

    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
    mock_server.login.assert_called_once_with("kate@example.com", "fake_app_password")

    sendmail_args = mock_server.sendmail.call_args[0]
    assert sendmail_args[0] == "kate@example.com"
    assert sendmail_args[1] == "kate@example.com"
    assert "test report" in sendmail_args[2]
    assert "Test Briefing" in sendmail_args[2]

print("PASS: send_email logs in and sends with correct sender/recipient/content")
