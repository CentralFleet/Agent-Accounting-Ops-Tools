
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
from pypdf import PdfWriter
import os

def send_message_to_channel(channel_id, message):
    """
    Send a message to a given Slack channel.

    Parameters:
        bot_token (str): The token for the Slack bot.
        channel_id (str): The ID of the channel to send the message to.
        message (str): The message to send to the channel.

    Returns:
        None
    """
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message,
            unfurl_links=False,  # Disable link previews
    unfurl_media=False 
        )
        print(f"Message successfully sent to channel {channel_id} on Slack")
    except SlackApiError as e:
        print(f"Error sending Message to slack: {e}")





def merge_pdfs(pdf_paths: list, output_path: str) -> int:
    """
    Merges multiple PDF files into one.
    """
    try:
        merger = PdfWriter()
        for pdf in pdf_paths:
            merger.append(pdf)
        merger.write(output_path)
        merger.close()

        for pdf in pdf_paths:
            os.remove(pdf)
        return 0

    except Exception as e:
        logging.error(f"Error merging PDFs: {str(e)}")
        return -1



def upload_invoice_to_slack(file_path, channel_id, slack_token, comment="Here is the latest version of the invoice!"):
    """
    Uploads a file to Slack.

    Args:
        file_path (str): Path to the file to be uploaded.
        channel_id (str): Slack channel ID where the file will be uploaded.
        slack_token (str): Slack bot token for authentication.
        comment (str): Initial comment for the uploaded file.

    Returns:
        dict: Response from Slack API or error details.
    """
    try:
        # Initialize Slack client
        client = WebClient(token=slack_token)

        # Upload the file to Slack
        response = client.files_upload_v2(
            file=file_path,
            title="Invoice Upload",
            channel=channel_id,
            initial_comment=comment
        )

        logging.info(f"Invoice uploaded to Slack successfully. Response: {response}")
        return response

    except SlackApiError as e:
        logging.error(f"Error uploading file to Slack: {e.response['error']}")
        return {"error": e.response["error"], "status_code": e.response["status"]}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": str(e), "status_code": 500}

