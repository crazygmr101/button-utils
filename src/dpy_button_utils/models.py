import re
from abc import ABC
from dataclasses import dataclass
from typing import List

from discord import PartialEmoji


@dataclass
class InteractionComponent(ABC):
    component_type: int

    def to_dict(self):
        raise NotImplemented


@dataclass
class ActionRow(InteractionComponent):
    def __init__(self, *components: InteractionComponent):
        self.components = components

    component_type: int = 1

    def to_dict(self):
        return {
            "type": 1,
            "components": [component.to_dict() for component in self.components]
        }


class Button(InteractionComponent):
    def __init__(self, style: int = None, label: str = None, emoji: PartialEmoji = None, custom_id: str = None,
                 url: str = None, disabled: bool = False):
        self.style = style
        self.label = label
        self.emoji = emoji
        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled
        if self.url:
            if self.style != ButtonStyle.link:
                raise ValueError("URLs are only supported in link buttons")
            else:
                self.style = ButtonStyle.link
        if self.style != ButtonStyle.link and not self.custom_id:
            raise ValueError("Non-link buttons must have a custom_id")
        if custom_id and not re.match(r"[\w-]{1,100}", custom_id):
            raise ValueError(r"custom_id must match [\w-]{1,100}")
        if not re.match(r".{1,80}", label):
            raise ValueError(r"label must match .{1,100}")

    disabled: bool = False
    component_type: int = 2

    def to_dict(self):
        dct = {
            "type": 2,
            "style": self.style,
            "label": self.label,
            "disabled": self.disabled
        }
        if self.emoji:
            dct.update({"emoji", self.emoji.to_dict()})
        if self.url:
            dct.update({"url": self.url})
        if self.custom_id:
            dct.update({"custom_id": self.custom_id})
        return dct


class ButtonStyle:
    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5