"""SendGrid email utility module."""

from loguru import logger
from typing import List, Dict, Optional, Union

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Cc, Bcc


class SendgridSender:
    """Encapsulates functions to send emails with Sendgrid."""

    def __init__(self, sendgrid_api_key: str):
        """
        Initializes the Sendgrid sender.

        Args:
            sendgrid_api_key: API key for SendGrid authentication
        """
        self.sendgrid_client = SendGridAPIClient(api_key=sendgrid_api_key)

    def send_email(
        self,
        source: str,
        destination: Union[str, List[str]],
        subject: str,
        text: str,
        html: str,
    ) -> Optional[Dict]:
        """
        Sends an email.

        Args:
            source: The source email account
            destination: The destination email account(s)
            subject: The email subject
            text: The email text content
            html: The email HTML content

        Returns:
            Response from the Sendgrid service or None if sending failed
        """
        message = Mail(
            from_email=source,
            to_emails=destination,
            subject=subject,
            plain_text_content=text,
            html_content=html,
        )
        try:
            response = self.sendgrid_client.send(message)
            logger.info(f"Sent mail from {source} to {destination}.")
            return response
        except Exception as e:
            logger.error(f"Couldn't send mail from {source} to {destination}: {e}")
            return None

    def send_templated_email(
        self,
        template_id: str,
        source: str,
        destination: Union[str, List[str]],
        template_data: Dict,
    ) -> Optional[Dict]:
        """
        Sends an email based on a template. A template contains replaceable tags
        each enclosed in two curly braces, such as {{name}}. The template data passed
        in this function contains key-value pairs that define the values to insert
        in place of the template tags.

        Args:
            template_id: The SendGrid template ID
            source: The source email account
            destination: The destination email account(s)
            template_data: The template data for variable substitution

        Returns:
            Response from the Sendgrid service or None if sending failed
        """
        message = Mail(
            from_email=source,
            to_emails=destination,
        )
        message.dynamic_template_data = template_data
        message.template_id = template_id
        try:
            response = self.sendgrid_client.send(message)
            logger.info(f"Sent templated mail from {source}")
            return response
        except Exception as e:
            logger.error(f"Couldn't send templated mail from {source}: {e}")
            return None

    def create_recipients(
        self,
        to: List[str],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> List:
        """
        Creates the recipients for the email.

        Args:
            to: The list of primary recipients
            cc: The list of CC recipients
            bcc: The list of BCC recipients

        Returns:
            List of recipient objects
        """
        recipients = []
        if to:
            recipients.extend([To(email) for email in to])
        if cc:
            recipients.extend([Cc(email) for email in cc])
        if bcc:
            recipients.extend([Bcc(email) for email in bcc])
        return recipients
