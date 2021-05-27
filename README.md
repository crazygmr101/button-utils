# Usage

## ButtonPaginator

```python
from discord.ext import commands
from dpy_button_utils import ButtonPaginator

bot = commands.Bot(command_prefix="!", help_command=None)

@bot.command()
async def page_plain_text(ctx: commands.Context):
    paginator = ButtonPaginator(bot, messages=[f"Option {x}" for x in range(10)], timeout=10)
    await paginator.run(ctx)


@bot.command()
async def page_embeds(ctx: commands.Context):
    paginator = ButtonPaginator(bot, embeds=[
        discord.Embed(title="bonk", description=f"Option {x}") for x in range(10)
    ])
    await paginator.run(ctx)


bot.run("TOKEN")
```

After the paginator is done, you can access the page it left off on with `paginator.counter`.

## ButtonConfirmation

```python
from discord.ext import commands

from dpy_button_utils.confirmation import ButtonConfirmation

bot = commands.Bot(command_prefix="!", help_command=None)

@bot.command()
async def confirm(ctx: commands.Context):
    if await ButtonConfirmation(ctx, "Do the bad thing?", destructive=True, confirm="YES", cancel="no pls").run():
        await ctx.send("yes :D")
    else:
        await ctx.send(":(")


@bot.command()
async def confirm2(ctx: commands.Context):
    if await ButtonConfirmation(ctx, "Do the thing?", destructive=False, confirm="YES", cancel="no pls").run():
        await ctx.send("yes :D")
    else:
        await ctx.send(":(")

bot.run("TOKEN")
```

`ButtonConfirmation` takes a few different keyword arguments, after the `Context` and `message`.
 
 - `destructive` - can either be `True` or `False`. `True` causes a red confirm button, and `False` causes a blue one
 - `timeout` - Time in seconds for the confirmation to auto-cancel
 - `confirm` - Confirmation button label
 - `cancel` - Cancel button label
 - `confirm_message` - Text to change to on a confirmation
 - `cancel_message` - Text to change to on a cancel
 
 The defaults are:
 - `destructive` - False
 - `timeout` - 60
 - `confirm` - Confirm
 - `cancel` - Cancel
 - `confirm_message` - `None` - this appends `Confirmed` to the original message
 - `cancel_message` - `None` - this appends `Cancelled` to the original message