from __future__ import annotations

import asyncio
from typing import List, Union

import discord
from discord import ui
from discord.ext import commands


class ButtonPaginator:
    def __init__(self, _ctx: commands.Context, *, messages: List[str] = None,
                 embeds: List[discord.Embed] = None, timeout: int = 60):
        if not messages and not embeds:
            raise ValueError("You must pass messages or embeds")
        if messages and embeds:
            raise ValueError("You must pass only one of messages or embeds")
        self._ctx = _ctx
        self._pages = messages or embeds
        self._timeout = timeout
        self.paginator = PaginatorView(messages=self._pages, user=self._ctx.author, timeout=self._timeout)
        self._timed_out = False

    @property
    def timed_out(self) -> bool:
        return self._timed_out

    @property
    def current(self) -> int:
        return self.paginator.current_index

    async def run(self) -> None:
        """
        Run the paginator
        :rtype: bool
        :return: True if paginator exists normally, and False if it timed out
        """
        message = await self._ctx.send(
            self.paginator.current if not self.paginator.is_embeds else None,
            embed=self.paginator.current if self.paginator.is_embeds else None,
            view=self.paginator
        )
        self._timed_out = await self.paginator.wait()

        await message.edit(
            content=self.paginator.current if not self.paginator.is_embeds else None,
            embed=self.paginator.current if self.paginator.is_embeds else None,
            view=self.paginator
        )

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


class PaginatorView(ui.View):
    def __init__(self, messages: Union[List[str], List[discord.Embed]], user: discord.Member, *args, **kwargs):
        super(PaginatorView, self).__init__(*args, **kwargs)
        self.is_embeds = isinstance(messages[0], discord.Embed)
        self.messages = messages
        self._current = 0
        self._user = user.id
        self._event = asyncio.Event()

    @property
    def current(self) -> Union[str, discord.Embed]:
        return self.messages[self._current]

    @property
    def current_index(self) -> int:
        return self._current

    @ui.button(label="<<", style=discord.ButtonStyle.secondary)
    async def _first(self, button: ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self._user:
            return
        self._current = 0
        await self._refresh(interaction.message)

    @ui.button(label="<", style=discord.ButtonStyle.secondary)
    async def _previous(self, button: ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self._user:
            return
        self._current = max(self._current - 1, 0)
        await self._refresh(interaction.message)

    @ui.button(label="x", style=discord.ButtonStyle.danger)
    async def _stop(self, button: ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self._user:
            return
        self._stop.disabled = True
        self._next.disabled = True
        self._last.disabled = True
        self._first.disabled = True
        self._previous.disabled = True
        await interaction.message.edit(
            content=self.messages[self._current] if not self.is_embeds else None,
            embed=self.messages[self._current] if self.is_embeds else None,
            view=self
        )
        self.stop()

    async def on_timeout(self) -> None:
        self._stop.disabled = True
        self._next.disabled = True
        self._last.disabled = True
        self._first.disabled = True
        self._previous.disabled = True

    @ui.button(label=">", style=discord.ButtonStyle.secondary)
    async def _next(self, button: ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self._user:
            return
        self._current = min(self._current + 1, len(self.messages) + 1)
        await self._refresh(interaction.message)

    @ui.button(label=">>", style=discord.ButtonStyle.secondary)
    async def _last(self, button: ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self._user:
            return
        self._current = len(self.messages) - 1
        await self._refresh(interaction.message)

    async def _refresh(self, message: discord.Message):
        self._previous.disabled = self._current == 0
        self._first.disabled = self._current == 0
        self._next.disabled = self._current == len(self.messages) - 1
        self._last.disabled = self._current == len(self.messages) - 1
        await message.edit(
            content=self.messages[self._current] if not self.is_embeds else None,
            embed=self.messages[self._current] if self.is_embeds else None,
            view=self
        )
