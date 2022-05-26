import asyncio
import aiohttp
import re
import typing

import discord
import json
import datetime
import random
import string
import collections
from discord.ext import commands

from config.constants.constants import Role, Misc

from config.bot_secrets import user_collection
from utils.colour import Colour


def staff_check(ctx: commands.Context):
    if not ctx.guild or ctx.guild.id != Misc.GUILD_ID:
        return False
    roles = ids(ctx.author.roles)
    return list_one(roles, *Role.MOD, *Role.ADMIN, *Role.BOT_DEV)

staff_only = commands.check(staff_check)


def bot_dev_check(ctx: commands.Context):
    if not ctx.guild or ctx.guild.id != Misc.GUILD_ID:
        return False
    roles = ids(ctx.author.roles)
    return list_one(roles, *Role.BOT_DEV, *Role.ADMIN)

bot_dev_only = commands.check(bot_dev_check)


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill="█", print_end="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    if iteration == total:
        print(f'\r{Colour.PURPLE}Loading Complete:             |{bar}| {percent}% {suffix}{Colour.END}', end=print_end)
    elif iteration in [0, 1]:
        print(f'\r{Colour.PURPLE}{prefix} |{bar}| {percent}%   {suffix}{Colour.END}', end=print_end)
    else:
        print(f'\r{Colour.PURPLE}{prefix} |{bar}| {percent}%  {suffix}{Colour.END}', end=print_end)


class MemberUserConverter(commands.Converter):
    async def convert(self, ctx, argument) -> typing.Union[discord.Member, discord.User]:
        try:
            return await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:
            try:
                return await commands.UserConverter().convert(ctx, argument)
            except commands.UserNotFound:
                raise commands.UserInputError


class DeltaTemplate(string.Template):
    delimiter = "%"


# noinspection SpellCheckingInspection
def strfdelta(tdelta, fmt):
    d = {"Y": tdelta.days // 365, "D": int(tdelta.days) % 365}
    d["H"], rem = divmod(tdelta.seconds, 3600)
    d["M"], d["S"] = divmod(rem, 60)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


async def get_user(user):
    try:
        await user_collection.insert_one({
            "_id": str(user.id),
            # levelling data
            "experience": 0,
            "weekly": 0,
            "level": 1,
            "last_message": 0,
            # points data
            "points": 0,
            "last_points": 0,
        })
    finally:
        return await user_collection.find_one({"_id": str(user.id)})


def leaderboard_pages(bot, guild: discord.Guild, users, *, key="level", prefix="", suffix="",
                      title="XP leaderboard",
                      field_name="Gain XP by chatting"):
    entries = []
    lb_pos = 1
    for i, user in enumerate(users):
        if not (member := guild.get_member(int(user["_id"]))):
            continue
        entries.append(f"**{lb_pos}: {member}** - {prefix}{user[key]:,}{suffix}\n")
        lb_pos += 1
    embeds = [discord.Embed(colour=0x00FF00).set_author(name=title, icon_url=guild.icon_url)]
    values = [""]
    embed_index = 0
    for i, entry in enumerate(entries):
        values[embed_index] += entry
        if not ((i + 1) % 15) and i != 0:
            embeds.append(discord.Embed(colour=0x00FF00).set_author(name=title, icon_url=guild.icon_url))
            embed_index += 1
            values.append("")
    embeds = embeds[:16]
    for i, embed in enumerate(embeds):
        embed.set_footer(text=f"page {i + 1} of {len(embeds)}").add_field(name=field_name, value=values[i],
                                                                          inline=False)
    return embeds


def list_one(_list, *items):
    for item in items:
        if item in _list:
            return True
    return False


def nano_id(length=20):
    return ''.join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))


def get_file_json(filename: str = "config/data/config") -> dict:
    with open(f"{filename}.json", encoding="utf-8") as f:
        return json.load(f)


def save_file_json(data, filename: str = "config/data/config"):
    with open(f"{filename}.json", 'w') as f:
        json.dump(data, f)


class RoleConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> discord.Role:
        role = None
        try:
            role = await commands.RoleConverter().convert(ctx, argument)
        except commands.RoleNotFound:
            role_list_lower = {z.name.lower(): z for z in ctx.guild.roles}
            if argument.lower() in role_list_lower:
                role = role_list_lower[argument.lower()]
            else:
                candidates = []
                for name in role_list_lower:
                    if argument.lower() in name:
                        candidates.append(role_list_lower[name])
                if len(candidates) == 1:
                    role = candidates[0]
                elif len(candidates) > 1:
                    await ctx.send(embed=discord.Embed(title="Which role?",
                                                       description="\n".join([f"{i + 1} : {z.mention}" for i, z in
                                                                              enumerate(candidates)]),
                                                       colour=discord.Colour.green()))
                    try:
                        res: discord.Message = await ctx.bot.wait_for('message', check=lambda
                            message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id,
                                                                      timeout=60)
                        number = int(res.content)
                        role = candidates[number - 1]
                    except asyncio.TimeoutError:
                        await ctx.send("Timed out")
                    except (ValueError, TypeError, IndexError):
                        await ctx.send("Invalid index")
        finally:
            if role:
                return role
            raise commands.RoleNotFound(argument)


def ids(items):
    return [z.id for z in items]


class Embed(discord.Embed):
    def __init__(self, user: discord.User, **kwargs):
        self.user = user
        super().__init__(**kwargs)

    def auto_author(self):
        self.set_author(name=self.user.__str__(), icon_url=self.user.avatar_url)
        return self

    def timestamp_now(self):
        self.timestamp = datetime.datetime.now()
        return self


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if isinstance(argument, int):
            return argument
        _time = string_to_seconds(argument)
        if _time:
            return _time
        else:
            raise commands.UserInputError


def string_to_seconds(_string):
    _time = 0
    times = {
        "w": 604800,
        "d": 86400,
        "h": 3600,
        "m": 60,
        "s": 1,
    }
    regex = r" ?(?P<time>(?P<number>\d+) ?(?P<period>d|h|m|s)) ?"
    _string = _string.lower()
    match = re.match(regex, _string)
    if match is None:
        return None
    while match:
        _time += int(match.group('number')) * times[match.group('period')]
        _string = _string[len(match.group('time')):]
        match = re.match(regex, _string)
    return _time


async def get_json_api(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

class MessageOrReplyConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str):
        message: discord.Message = None
        try:
            message = await commands.MessageConverter().convert(ctx, argument)
        except commands.MessageNotFound:
            message = ctx.message.reference
            message = message.cached_message if message else message
        if message is None:
            raise commands.MessageNotFound(argument)
        return message

