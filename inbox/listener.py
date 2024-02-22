from typing import List
import time
from inbox.provider.generic import InboxProvider
from inbox.action.message import MessageAction

class InboxListener:
    def __init__(self, provider: InboxProvider, actions: List[MessageAction]):
        self.provider = provider
        self.actions = actions

    def listen(self):
        print(f"InboxListener started listening with provider: {self.provider.__class__.__name__} and actions: {[action.__class__.__name__ for action in self.actions]}")
        while True:
            print("Syncing inbox...")
            emails = self.provider.sync_inbox()
            if not emails:
                # If no emails are returned, wait for 2 minutes before the next sync
                print("No emails found, waiting for 2 minutes before next sync...")
                time.sleep(120)
                continue

            print("Processing {} emails...".format(len(emails)))
            for email in emails:
                for action in self.actions:
                    print("Processing email with action: {}".format(action.__class__.__name__))
                    action.processMessage(email)
            print("Finished processing emails, continuing to next sync...")
