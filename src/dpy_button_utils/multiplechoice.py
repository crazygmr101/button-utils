import asyncio
from typing import List

import discord
from discord.ext import commands
from discord.http import Route
from .models import ActionRow, ButtonStyle, Button, InteractionComponent


class ButtonMultipleChoice:
    class _CustomRoute(Route):
        BASE = "https://discord.com/api/v9"

    def __init__(self, ctx: commands.Context, content: str, *components: InteractionComponent,
                 timeout: int = 60):
        self.components = components
        self.ctx = ctx
        self._bot = ctx.bot
        self._http = self._bot.http
        self.content = content
        self.timeout = timeout
        self.msg = None

    async def run(self) -> Button:
        # send the original message
        msg = (await self._http.request(
            ButtonMultipleChoice._CustomRoute("POST", f"/channels/{self.ctx.channel.id}/messages"),
            json={
                "content": self.content,
                "components": [component.to_dict() for component in self.components],
                "allowed_mentions": discord.AllowedMentions.none().to_dict()
            }
        ))["id"]

        message_edit = ButtonMultipleChoice._CustomRoute("PATCH", f"/channels/{self.ctx.channel.id}/messages/{msg}")

        while True:
            try:
                event = await self._bot.wait_for("socket_response", timeout=self.timeout,
                                                 check=lambda e: (
                                                         e["t"] == "INTERACTION_CREATE" and
                                                         e["d"].get("message", {}).get("id", None) == msg and
                                                         "custom_id" in e["d"].get("data", {})
                                                 ))
                await self._http.request(ButtonMultipleChoice._CustomRoute(
                    "POST",
                    f"/interactions/{event['d']['id']}/{event['d']['token']}/callback"),
                    json={"type": 6})
                if event["d"].get("member", {}).get("user", {}).get("id", None) != str(self.ctx.author.id):
                    continue
                button_clicked = event["d"]["data"]["custom_id"]
            except asyncio.TimeoutError:
                button_clicked = None

            row: ActionRow
            button: Button
            for row in self.components:
                for button in row.components:
                    button.disabled = True
                    if button.custom_id != button_clicked and button.style != ButtonStyle.link:
                        button.style = ButtonStyle.secondary
                    if button.custom_id == button_clicked:
                        button.style = ButtonStyle.success

            await self._http.request(message_edit, json={
                "content": self.content,
                "components": [component.to_dict() for component in self.components],
                "allowed_mentions": discord.AllowedMentions.none().to_dict()
            })

            self.msg = int(msg)
            return button_clicked
