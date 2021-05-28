from __future__ import annotations

import asyncio
from typing import List

import discord
from discord.ext import commands
from discord.http import Route


class ButtonPaginator:
    class _CustomRoute(Route):
        BASE = "https://discord.com/api/v9"

    def __init__(self, _ctx: commands.Context, *, messages: List[str] = None,
                 embeds: List[discord.Embed] = None, timeout: int = 60):
        if embeds and messages:
            raise ValueError("You can only pass either messages or embeds")
        self._embeds = embeds
        self.messages = messages
        self.timeout = timeout
        if self._embeds:
            self.responses = [{"embed": embed.to_dict()} for embed in self._embeds]
        else:
            self.responses = [{"content": content} for content in self.messages]
        self.buttons = {
            "begin": ["<<", lambda x: 0],
            "previous": ["<", lambda x: max(0, x - 1)],
            "stop": ["X", lambda x: None],
            "next": [">", lambda x: min(len(self.responses) - 1, x + 1)],
            "end": [">>", lambda x: len(self.responses) - 1]
        }
        for response in self.responses:
            response.update({"allowed_mentions": discord.AllowedMentions.none().to_dict(),
                             "components": [{"type": 1, "components": [
                                 {"type": 2, "label": v[0], "custom_id": k, "style": 4 if k == "stop" else 2}
                                 for k, v in self.buttons.items()
                             ]}]})
        self._bot: commands.Bot = _ctx.bot
        self._http = self._bot.http
        self.counter = 0
        self.ctx = _ctx

    async def run(self):
        msg = (await self._http.request(
            ButtonPaginator._CustomRoute("POST", f"/channels/{self.ctx.channel.id}/messages"),
            json=self.responses[0]
        ))["id"]

        while True:
            try:
                event = await self._bot.wait_for("socket_response", timeout=self.timeout,
                                                 check=lambda e: (
                                                         e["t"] == "INTERACTION_CREATE" and
                                                         e["d"].get("message", {}).get("id", None) == msg and
                                                         "custom_id" in e["d"].get("data", {})
                                                 ))
                await self._http.request(
                    ButtonPaginator._CustomRoute("POST",
                                                 f"/interactions/{event['d']['id']}/{event['d']['token']}/callback"),
                    json={"type": 6})
                if event["d"].get("member", {}).get("user", {}).get("id", None) != str(self.ctx.author.id):
                    continue
                button_clicked = event["d"]["data"]["custom_id"]
            except asyncio.TimeoutError:
                button_clicked = "stop"
            message_edit = ButtonPaginator._CustomRoute("PATCH", f"/channels/{self.ctx.channel.id}/messages/{msg}")

            if button_clicked != "stop":
                self.counter = self.buttons[button_clicked][1](self.counter)

            current_response = self.responses[self.counter]

            if button_clicked == "stop":
                current_response["components"] = {}

            await self._http.request(message_edit, json=current_response)

            if button_clicked == "stop":
                break

    @classmethod
    def from_content(cls, ctx: commands.Context, content: str, *, timeout=60, max_chars=2000, min_chars=1500,
                     splitter=" ", fmt: str = "{content}") -> "ButtonPaginator":
        """
        Makes a ButtonPaginator from a long block of content

        For fmt, there are a few placeholders:
         - {current_page} - current page number (0 indexed)
         - {current_page_plus_one} - current page number (1 indexed)
         - {total_pages} - total number of pages
         - {content} - the current content

         NOTE: the length is counted on the **content** only, before any placeholders.

        :param ctx: the Context for the command
        :param content: the content
        :param timeout: time it takes for the paginator to stop after the last valid interaction
        :param max_chars: max chars per page
        :param min_chars: min chars per page
        :param splitter: the character to split on
        :param fmt: the format to use on each page.
        :return: a ButtonPaginator
        """
        content_list = []
        split = content.split(splitter)
        current = ""
        for chunk in split:
            if len(current) + len(chunk) > max_chars:
                if len(current) < min_chars:
                    content_list.append(current + splitter + chunk[:min_chars - len(current)])
                    current = chunk[min_chars - len(current):]
                else:
                    content_list.append(current)
                    current = chunk
            else:
                current += splitter + chunk
        content_list.append(current)

        return cls(ctx, messages=[
            fmt.format(
                content=page,
                current_page=n,
                current_page_plus_one=n + 1,
                total_pages=len(content_list))
            for n, page in enumerate(content_list)], timeout=timeout)
