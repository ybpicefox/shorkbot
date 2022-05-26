import discord
from discord.ext import commands

from config.constants.constants import Channel
from utils.utils import string_to_seconds as sts, Embed, TimeConverter, staff_only, RoleConverter, bot_dev_only
from utils import moderation_utils
import asyncio
from config.bot_secrets import moderation_collection, user_collection
import typing
import os


class Staff(commands.Cog):  # general staff-only commands that don't fit into another category
    def __init__(self, bot, hidden):
        self.hidden = hidden
        self.bot: commands.Bot = bot



    @commands.command(aliases=["say"])
    @staff_only
    async def send(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, message: str):
        """Make the bot send a message"""
        channel = channel if channel else ctx.channel
        if not ctx.author.permissions_in(channel).send_messages:
            raise commands.MissingPermissions(["manage_messages"])
        msg = await channel.send(message)
        if channel.id != ctx.channel.id:
            await ctx.send(msg.jump_url)

    @commands.command()
    @staff_only
    async def reply(self, ctx, message: discord.Message, ping: typing.Optional[bool] = True, *, text: str):
        """Make the bot reply to a message"""
        if not ctx.author.permissions_in(message.channel).send_messages:
            raise commands.MissingPermissions(["manage_messages"])
        msg = await message.reply(content=text, mention_author=ping)
        if message.channel.id != ctx.channel.id:
            await ctx.send(msg.jump_url)

    @commands.command()
    @staff_only
    async def embed(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, message: str):
        """Make the bot send an embed"""
        channel = channel if channel else ctx.channel
        if not ctx.author.permissions_in(channel).send_messages:
            raise commands.MissingPermissions(["manage_messages"])
        msg = await channel.send(embed=discord.Embed)
        if channel.id != ctx.channel.id:
            await ctx.send(msg.jump_url)


    @commands.command()
    @staff_only
    async def slowmode(self, ctx, time="off"):
        """Change the channel's slowmode"""
        if time.lower() == "off":
            await ctx.channel.edit(slowmode_delay=0)
            return await ctx.send(f"slowmode has been removed from {ctx.channel.mention} by {ctx.author.mention}")
        else:
            timer = sts(time)
            if not timer:
                return await ctx.send("invalid slowmode time")
            else:
                await ctx.channel.edit(slowmode_delay=timer)
                return await ctx.send(f"slowmode has been set to `{time}` by {ctx.author.mention}")

    @commands.command()
    @staff_only
    async def role(self, ctx, user: discord.Member, *, role: RoleConverter):
        """Give someone a role"""
        if role.permissions.manage_messages or role.permissions.administrator or role.name.lower() == "muted":
            return await ctx.send("You are not allowed to give that role")
        try:
            await user.add_roles(role, reason=f"Given by {ctx.author}")
            await ctx.send(embed=discord.Embed(title="Role added :scroll:",
                                               description=f":white_check_mark: Gave {role.mention} to {user.mention}",
                                               colour=0xfb00fd))
            await ctx.message.delete()
        except discord.Forbidden:
            return await ctx.send("I do not have permission to give that role to that user")

    @commands.command()
    @staff_only
    async def removerole(self, ctx, user: discord.Member, *, role: RoleConverter):
        """Remove a role from someone"""
        if role.permissions.manage_messages or role.permissions.administrator or role.name.lower() == "muted":
            return await ctx.send("You are not allowed to remove that role")
        try:
            await user.remove_roles(role, reason=f"Removed by {ctx.author}")
            await ctx.send(embed=discord.Embed(title="Role removed :scroll:",
                                               description=f":white_check_mark: Removed {role.mention} from {user.mention}",
                                               color=0xfb00fd))
            await ctx.message.delete()
        except discord.Forbidden:
            return await ctx.send("I do not have permission to remove that role from that user")


    @commands.command()
    @staff_only
    async def purge(self, ctx, limit: int):
        """Purge messages in a channel"""

        def check(m):
            return not m.pinned

        await ctx.channel.purge(limit=limit + 1, check=check)
        await asyncio.sleep(1)
        chat_embed = discord.Embed(description=f"Cleared {limit} messages", color=0xfb00fd)
        chat_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=chat_embed)
        log_embed = discord.Embed(title="Purge", description=f"{limit} messages cleared from {ctx.channel.mention}")
        log_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        await ctx.guild.get_channel(Channel.MOD_LOGS).send(embed=log_embed)


    @commands.command()
    @staff_only
    async def modhelp(self, ctx):
        """View the help menu for all moderation commands"""
        bot: commands.Bot = ctx.bot
        mod_cogs = [bot.get_cog(z) for z in bot.cogs]
        mod_cogs = filter(lambda x: x.hidden, mod_cogs)
        embed = discord.Embed(title="Moderation Help!", colour=discord.Colour.gold())
        string = ""
        for cog in mod_cogs:
            cog_string = ""
            for cmd in cog.get_commands():
                cog_string += f"\n`{ctx.prefix}{cmd.name}`"
            string += f"\n**{cog.qualified_name}:**{cog_string}"
        embed.description = string
        await ctx.send(embed=embed)
        
    @commands.command(name="-pull")
    @bot_dev_only
    async def pull(self, ctx: commands.Context):
        if os.system("git pull origin master") == 0:
            await ctx.send("Successfully pulled from github. Do -reload to reload all cogs.")
        else:
            await ctx.send("Pull unsuccessful. Check logs for more info.")






    @commands.group(aliases=["-c"])
    @staff_only
    async def config(self, ctx):
        """Edit the config"""
        if not ctx.invoked_subcommand:
            await ctx.send(
                "\n".join([f"- {z.name}{'*' if isinstance(z, commands.Group) else ''}" for z in self.config.commands]))
        else:
            await ctx.send("Successfully updated configuration")
            await moderation_utils.update_config()



    @config.command()
    async def mutedRole(self, ctx, *, role: discord.Role):
        await moderation_collection.update_one({"_id": "config"}, {"$set": {"muteRole": role.id}})

    @config.command()
    async def deleteWarnsAfter(self, ctx, _time: TimeConverter):
        await moderation_collection.update_one({"_id": "config"}, {"$set": {"deleteWarnsAfter": _time}})

    @config.group(invoke_without_command=True)
    async def punishForWarns(self, ctx):
        await ctx.send("\n".join(
            [f"- {z.name}{'*' if isinstance(z, commands.Group) else ''}" for z in self.punishForWarns.commands]))

    @punishForWarns.command(name="add")
    async def p_add(self, ctx, warns: int, duration: TimeConverter, _type="mute"):
        await moderation_collection.update_one({"_id": "config"}, {
            "$set": {"punishForWarns.{}".format(warns): {"type": _type, "duration": duration}}})

    @punishForWarns.command(name="remove")
    async def p_remove(self, ctx, warns: int):
        await moderation_collection.update_one({"_id": "config"}, {"$unset": {"punishForWarns.{}".format(warns): ""}})

    @config.group(invoke_without_command=True)
    async def automod(self, ctx):
        await ctx.send(
            "\n".join([f"- {z.name}{'*' if isinstance(z, commands.Group) else ''}" for z in self.automod.commands]))

    @automod.group(invoke_without_command=True)
    async def mentions(self, ctx):
        await ctx.send(
            "\n".join([f"- {z.name}{'*' if isinstance(z, commands.Group) else ''}" for z in self.mentions.commands]))

    @mentions.command(name="punishment")
    async def m_punishment(self, ctx, action: str = "delete"):
        await moderation_collection.update_one({"_id": "config"},
                                               {"$set": {"mentions.action": action if action == "warn" else "delete"}})

    @mentions.command()
    async def value(self, ctx, val: int):
        await moderation_collection.update_one({"_id": "config"}, {"$set": {"mentions.val": val}})

    @mentions.command(name="allowChannel")
    async def m_allowChannel(self, ctx, channel: discord.TextChannel):
        await moderation_collection.update_one({"_id": "config"}, {"$push": {"mentions.allowed_channels": channel.id}})

    @mentions.command(name="disallowChannel")
    async def m_disallowChannel(self, ctx, channel: discord.TextChannel):
        await moderation_collection.update_one({"_id": "config"}, {"$pull": {"mentions.allowed_channels": channel.id}})

    @automod.group(invoke_without_command=True)
    async def invites(self, ctx):
        await ctx.send(
            "\n".join([f"- {z.name}{'*' if isinstance(z, commands.Group) else ''}" for z in self.invites.commands]))

    @invites.command(name="punishment")
    async def i_punishment(self, ctx, action: str = "delete"):
        await moderation_collection.update_one({"_id": "config"},
                                               {"$set": {"invites.action": action if action == "warn" else "delete"}})

    @invites.command(name="allowChannel")
    async def i_allowChannel(self, ctx, channel: discord.TextChannel):
        await moderation_collection.update_one({"_id": "config"}, {"$push": {"invites.allowed_channels": channel.id}})

    @invites.command(name="disallowChannel")
    async def i_disallowChannel(self, ctx, channel: discord.TextChannel):
        await moderation_collection.update_one({"_id": "config"}, {"$pull": {"invites.allowed_channels": channel.id}})

    @automod.group(invoke_without_command=True)
    async def badWords(self, ctx):
        await ctx.send(
            "\n".join([f"- {z.name}{'*' if isinstance(z, commands.Group) else ''}" for z in self.badWords.commands]))

    @badWords.command(name="add")
    async def b_add(self, ctx, word: str, action: str = "delete"):
        await moderation_collection.update_one({"_id": "config"}, {"$set": {"badWords.{}".format(word.lower()): action}})

    @badWords.command(name="remove")
    async def b_remove(self, ctx, word: str):
        await moderation_collection.update_one({"_id": "config"}, {"$unset": {"badWords.{}".format(word.lower()): ""}})



def setup(bot):
    bot.add_cog(Staff(bot, True))
