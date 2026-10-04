"""Send sanitized operator alerts through the connected Composio Gmail CLI.

Set ALERT_TO_EMAIL (who gets alerts) and ALERT_FROM_EMAIL (the Gmail account connected
in Composio). ALERT_DASHBOARD_URL is optional: a link to your host's logs or project page.
"""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def show_details():
    for name in ('show.config.json', 'automation/show.config.json'):
        path = ROOT / name
        if path.exists():
            cfg = json.loads(path.read_text())
            return cfg.get('title') or 'Podcast', cfg.get('feedUrl', '')
    return 'Podcast', ''


def send_alert(stage, at, test=False, detail=None):
    recipient = os.environ.get('ALERT_TO_EMAIL')
    sender = os.environ.get('ALERT_FROM_EMAIL')
    if not recipient or not sender:
        raise RuntimeError('Set ALERT_TO_EMAIL and ALERT_FROM_EMAIL to send alerts')
    bootstrap = os.environ.get('COMPOSIO_USER_DATA_JSON')
    if bootstrap:
        destination = Path.home() / '.composio/user_data.json'
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination.write_text(json.dumps(json.loads(bootstrap)))
        destination.chmod(0o600)
    title, feed = show_details()
    links = ''
    if os.environ.get('ALERT_DASHBOARD_URL'):
        links += f"\n\nDashboard: {os.environ['ALERT_DASHBOARD_URL']}"
    if feed:
        links += f'\nFeed: {feed}'
    payload = {
        'recipient_email': recipient,
        'from_email': sender,
        'subject': f'{title}: alert delivery test' if test else f'{title} needs attention: {stage}',
        'body': ('This is a test of the podcast failure alert. No episode failure is being reported.'
                 if test else f'{detail} Checked at {at}.' if detail else
                 f'The podcast automation failed during {stage} at {at}. '
                 'If authentication failed, sign into NotebookLM again and replace the NOTEBOOKLM_MASTER_TOKEN_JSON secret. '
                 'For publication failures, inspect the live feed before rerunning to avoid duplicates.')
                 + links,
        'is_html': False,
    }
    result = subprocess.run(['composio', 'execute', 'GMAIL_SEND_EMAIL', '-d', '-'],
                            input=json.dumps(payload), capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Alert send failed; inspect Composio delivery before retrying')
    value = json.loads(result.stdout)
    if value.get('successful') is False or value.get('error'):
        raise RuntimeError('Alert provider rejected send')
    return True


if __name__ == '__main__':
    send_alert('test', '', test=True)
    print('Alert delivery test accepted by Gmail.')
