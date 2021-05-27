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