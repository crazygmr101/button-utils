import asyncio
from typing import List

import discord
from discord.ext import commands
from discord.http import Route


class ButtonPaginator:
    class _CustomRoute(Route):
        BASE = "https://discord.com/api/v9"

    def __init__(self, _bot: commands.Bot, *, messages: List[str] = None,
                 embeds: List[discord.Embed] = None, timeout: int = 60):
        if embeds and messages:
            raise ValueError("You can only pass either messages or embeds")
        self.embeds = embeds
        self.messages = messages
        self.timeout = timeout
        if self.embeds:
            self.responses = [{"embed": embed.to_dict()} for embed in self.embeds]
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
        self.http = _bot.http
        self.bot = _bot

    async def run(self, ctx: commands.Context):
        msg = (await self.http.request(
            ButtonPaginator._CustomRoute("POST", f"/channels/{ctx.channel.id}/messages"),
            json=self.responses[0]
        ))["id"]
        counter = 0

        while True:
            try:
                event = await self.bot.wait_for("socket_response", timeout=self.timeout,
                                                check=lambda e: (
                                                        e["t"] == "INTERACTION_CREATE" and
                                                        e["d"].get("message", {}).get("id", None) == msg and
                                                        "custom_id" in e["d"].get("data", {})
                                                ))
                await self.http.request(
                    ButtonPaginator._CustomRoute("POST",
                                                 f"/interactions/{event['d']['id']}/{event['d']['token']}/callback"),
                    json={"type": 6})
                if event["d"].get("member", {}).get("user", {}).get("id", None) != str(ctx.author.id):
                    continue
                button_clicked = event["d"]["data"]["custom_id"]
            except asyncio.TimeoutError:
                button_clicked = "stop"
            message_edit = ButtonPaginator._CustomRoute("PATCH", f"/channels/{ctx.channel.id}/messages/{msg}")

            if button_clicked != "stop":
                counter = self.buttons[button_clicked][1](counter)

            current_response = self.responses[counter]

            if button_clicked == "stop":
                current_response["components"] = {}

            await self.http.request(message_edit, json=current_response)

            if button_clicked == "stop":
                break
