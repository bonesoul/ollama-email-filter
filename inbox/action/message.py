from abc import ABC, abstractmethod
from email.message import Message

from inbox.provider.generic import InboxProvider

class MessageAction(ABC):
    def __init__(self, provider: InboxProvider):
        self.provider = provider

    @abstractmethod
    def processMessage(self, email_message: Message):
        pass
