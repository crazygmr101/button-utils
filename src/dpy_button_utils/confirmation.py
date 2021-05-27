import asyncio

from discord.http import Route
from discord.ext import commands


class ButtonConfirmation:
    class _CustomRoute(Route):
        BASE = "https://discord.com/api/v9"

    def __init__(self, _ctx: commands.Context, message: str, *,
                 destructive: bool = False,
                 timeout: int = 60,
                 confirm: str = "Confirm",
                 cancel: str = "Cancel",
                 confirm_message: str = None,
                 cancel_message: str = None):
        self.destructive = destructive
        self.timeout = timeout
        self.message = message
        self.ctx = _ctx
        self._http = _ctx.bot.http
        self._bot = _ctx.bot
        self.confirm = confirm
        self.cancel = cancel
        self.confirm_message = confirm_message
        self.cancel_message = cancel_message
        self.msg = None

    async def run(self):
        msg = (await self._http.request(
            ButtonConfirmation._CustomRoute("POST", f"/channels/{self.ctx.channel.id}/messages"),
            json={
                "content": self.message,
                "components": [{"type": 1, "components": [
                    {"type": 2, "label": self.confirm, "custom_id": "confirm", "style": 4 if self.destructive else 1},
                    {"type": 2, "label": self.cancel, "custom_id": "cancel", "style": 2}
                ]}]
            }
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
                    ButtonConfirmation._CustomRoute("POST",
                                                    f"/interactions/{event['d']['id']}/{event['d']['token']}/callback"),
                    json={"type": 6})
                if event["d"].get("member", {}).get("user", {}).get("id", None) != str(self.ctx.author.id):
                    continue
                button_clicked = event["d"]["data"]["custom_id"]
            except asyncio.TimeoutError:
                button_clicked = "cancel"

            if button_clicked == "cancel":
                resp = {
                    "content": f"{self.message}\nCancelled" if not self.cancel_message else self.cancel_message,
                    "components": {}
                }
            else:
                resp = {
                    "content": f"{self.message}\nConfirmed" if not self.confirm_message else self.confirm_message,
                    "components": {}
                }

            message_edit = ButtonConfirmation._CustomRoute("PATCH", f"/channels/{self.ctx.channel.id}/messages/{msg}")

            await self._http.request(message_edit, json=resp)

            self.msg = int(msg)
            return button_clicked == "confirm"
