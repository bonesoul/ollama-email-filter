from abc import ABC, abstractmethod
from typing import List
from email.message import Message

class InboxProvider(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def sync_inbox(self, full_sync: bool = False) -> List[Message]:
        pass

    @abstractmethod
    def create_label(self, label_name: str) -> None:
        pass

    @abstractmethod
    def create_folder(self, folder_name: str) -> None:
        pass

    @abstractmethod
    def label_message(self, email_message: Message, label_ids: List[str]) -> None:
        pass

    @abstractmethod
    def get_message_labels(self, email_message: Message) -> List[str]:
        pass

    @abstractmethod
    def move_message_to_folder(self, email_message: Message, folder_id: str) -> None:
        pass

    @abstractmethod
    def has_emailed_before(self, email: str) -> bool:
        pass

    @abstractmethod
    def archive_message(self, email_message: Message) -> None:
        pass
