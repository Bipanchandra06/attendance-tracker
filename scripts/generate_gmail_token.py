"""Create a Gmail API refresh token for the deployment environment.

Usage:
    python scripts/generate_gmail_token.py path/to/client_secret.json

The printed refresh token belongs in Render and GitHub Actions secrets only.
Do not commit the client secret or generated token.
"""

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/generate_gmail_token.py path/to/client_secret.json')
    client_secret_path = Path(sys.argv[1])
    if not client_secret_path.exists():
        raise SystemExit(f'Client secret file not found: {client_secret_path}')

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    credentials = flow.run_local_server(port=0, access_type='offline', prompt='consent')
    print('\nGMAIL_CLIENT_ID=' + credentials.client_id)
    print('GMAIL_CLIENT_SECRET=' + credentials.client_secret)
    print('GMAIL_REFRESH_TOKEN=' + credentials.refresh_token)
    print('\nCopy these values into Render and GitHub Actions secrets. Do not commit them.')


if __name__ == '__main__':
    main()
