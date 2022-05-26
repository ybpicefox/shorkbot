import os
import sys

import discord
from discord.ext import commands

from utils import utils
from utils.colour import Colour
import time
import math
from config.bot_secrets import token, prefix, cogs
import traceback
from utils.utils import staff_only, bot_dev_only

intents = discord.Intents.default()
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix=prefix, case_insensitive=True, intents=intents)
bot.remove_command('help')

initial_extensions = ['cogs.level',
                      'cogs.tickets',
                      'cogs.automod',
                      'cogs.eval',
                      'cogs.moderation',
                      'cogs.logging',
                      'cogs.staff',
                      'cogs.useless',
                      'cogs.util']

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}', file=sys.stderr)
            traceback.print_exc()


@bot.event
async def on_command_error(ctx, error):
    # if command has local error handler, return
    if hasattr(ctx.command, 'on_error'):
        return

        # get the original exception
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.BotMissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'I need the **{}** permission(s) to run this command.'.format(fmt)
        await ctx.send(_message)
        return
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingAnyRole):
        roles = error.missing_roles if isinstance(error, commands.MissingAnyRole) else [error.missing_role]
        return await ctx.send(embed=discord.Embed(title=":x: Error! You must have one of these roles: :x:",
                                                  description="\n".join(roles),
                                                  colour=0xff0000))

    if isinstance(error, commands.DisabledCommand):
        await ctx.send('This command has been disabled.')
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please retry in {}s.".format(math.ceil(error.retry_after)))
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
        return

    if isinstance(error, commands.UserInputError):
        embed = discord.Embed(title=":x: Invalid Input!",
                              description=f"Correct usage: `-{ctx.command.qualified_name} {ctx.command.signature}`",
                              color=0xff0000)
        return await ctx.send(embed=embed)

    if isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send('This command cannot be used in direct messages.')
        except discord.Forbidden:
            pass
        return

    if isinstance(error, commands.CheckFailure):
        return await ctx.send("You do not have permission to use this command.")
    if isinstance(error, discord.Forbidden):
        return await ctx.send("I do not have permission to perform an action for that command")

    #     # ignore all other exception types, but print them to stderr
    print("EXCEPTION TRACE PRINT:\n{}".format(
        "".join(traceback.format_exception(type(error), error, error.__traceback__))))


@bot.event
async def on_ready():
    print(f"{Colour.YELLOW}Loading: {bot.user.name}!{Colour.END}\n")
    time.sleep(1)
    l = len(cogs)
    utils.print_progress_bar(0, l, prefix=f'\nInitializing:                ', suffix='Complete', length=50)
    for i, cog in enumerate(cogs):
        time.sleep(0.3)
        utils.print_progress_bar(i + 1, l, prefix=f'Loading:{" " * (20 - len(cog))} {cog}', suffix='Complete',
                                 length=50)
    print(f"{Colour.YELLOW}\nInitializing Bot, Please wait...{Colour.END}\n")
    print(f'{Colour.GREEN}Cogs loaded... Bot is now ready and waiting for prefix "."{Colour.END}')

    print(f'{Colour.GREEN}\n√ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √ √  {Colour.END}')
    return
    game = discord.Game("Minecraft")
    await client.change_presence(status=discord.Status.idle, activity=game)

@bot.command(name='reloade',
             description='Reloads bot',
             aliases=['-re'],
             hidden=True,
             case_insensitive=True)
@commands.guild_only()
@staff_only
async def reloade(ctx: commands.Context):
    """ Reloads cogs while bot is still online """
    user = ctx.author
    updated_cogs = ''
    l = len(cogs)
    utils.print_progress_bar(0, l, prefix='\nInitializing:', suffix='Complete', length=50)
    for i, cog in enumerate(cogs):
        utils.print_progress_bar(i + 1, l, prefix='Progress:', suffix='Complete', length=50)
        bot.unload_extension(cog)
        print("Reloading", cog)
        bot.load_extension(cog)
        updated_cogs += f'{cog}\n'
    print(f"\n{Colour.PURPLE}Initializing Bot, Please wait...{Colour.END}\n")
    print(f'{Colour.GREEN}Cogs loaded... Bot is now ready and waiting for prefix "."{Colour.END}')
    await ctx.send(f"`Cogs reloaded by:` {user.mention}")

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms ')

@bot.command(pass_context=True, name="-r")
@bot_dev_only
async def reload(ctx, *, msg):
    """Load a module."""
    await ctx.message.delete()
    try:
        if os.path.exists("custom_cogs/{}.py".format(msg)):
            bot.reload_extension("custom_cogs.{}".format(msg))
        elif os.path.exists("cogs/{}.py".format(msg)):
            bot.reload_extension("cogs.{}".format(msg))
        else:
            raise ImportError("No module named '{}'".format(msg))
    except Exception as e:
        await ctx.send('Failed to reload module: `{}.py`'.format(msg))
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Reloaded module: `{}.py`'.format(msg))


@bot.command(pass_context=True, name="-u")
@staff_only
async def unload(ctx, *, msg):
    """Unload a module"""
    await ctx.message.delete()
    try:
        if os.path.exists("cogs/{}.py".format(msg)):
            bot.unload_extension("cogs.{}".format(msg))
        elif os.path.exists("custom_cogs/{}.py".format(msg)):
            bot.unload_extension("custom_cogs.{}".format(msg))
        else:
            raise ImportError("No module named '{}'".format(msg))
    except Exception as e:
        await ctx.send('Failed to unload module: `{}.py`'.format(msg))
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Unloaded module: `{}.py`'.format(msg))


@bot.command(pass_context=True, name="-l")
@staff_only
async def load(ctx, *, msg):
    """Load a module"""
    await ctx.message.delete()
    try:
        if os.path.exists("cogs/{}.py".format(msg)):
            bot.load_extension("cogs.{}".format(msg))
        elif os.path.exists("custom_cogs/{}.py".format(msg)):
            bot.load_extension("custom_cogs.{}".format(msg))
        else:
            raise ImportError("No module named '{}'".format(msg))
    except Exception as e:
        await ctx.send('Failed to load module: `{}.py`'.format(msg))
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Loaded module: `{}.py`'.format(msg))
        
        
@bot.command()
async def serverinfo(ctx):
    name = str(ctx.guild.name)
    description = str(ctx.guild.description)

    id = str(ctx.guild.id)
    region = str(ctx.guild.region)
    memberCount = str(ctx.guild.member_count)

    icon = str(ctx.guild.icon_url)

    embed = discord.Embed(
        title=name + " Server Information",
        description=description,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=f"{ctx.guild.owner}", inline=True)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Region", value=region, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)

    await ctx.send(embed=embed)


bot.run(token, bot=True, reconnect=True)
