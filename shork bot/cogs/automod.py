import discord
from discord.ext import commands, tasks
from config.bot_secrets import moderation_collection
import time
from utils import moderation_utils, utils
import re

INVITE_REGEX = r"discord.gg\/(\w{6})"


# noinspection SpellCheckingInspection
class Automod(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.hidden = True
        self.bot: commands.Bot = bot
        self.delete_warns.start()
        self.timed_punishments.start()

    @commands.Cog.listener()
    async def on_ready(self):
        await moderation_utils.update_config()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not (message.guild or isinstance(message.author, discord.Member)) or type(message.author) == discord.User or message.author.bot:
            return
        if utils.staff_check(message):
            return
        ctx: commands.Context = await self.bot.get_context(message)
        # noinspection PyPropertyAccess
        ctx.author = message.guild.me
        config = await moderation_utils.get_config()
        if config["mentions"]["val"] <= len(message.mentions) and message.channel.id not in config["mentions"][
                "allowed_channels"]:
            await ctx.invoke(self.bot.get_command('warn'), message.author, reason="Mass mention")
        if config["invites"]["action"] == "warn" and message.channel.id not in config["invites"][
                "allowed_channels"] and re.match(INVITE_REGEX, message.content, re.IGNORECASE):
            await ctx.invoke(self.bot.get_command('warn'), message.author, reason="Invite link")
        if config["invites"]["action"] == "delete" and message.channel.id not in config["invites"][
                "allowed_channels"] and re.match(INVITE_REGEX, message.content, re.IGNORECASE):
            await message.delete()
        for word in config["badWords"]:
            if re.findall(word, message.content, flags=re.IGNORECASE):
                if config["badWords"][word] == "delete":
                    await message.delete()
                elif config["badWords"][word] == "warn":
                    await ctx.invoke(self.bot.get_command('warn'), message.author, reason="Disallowed word/phrase")
                elif config["badWords"][word] == "kick":
                    await ctx.invoke(self.bot.get_command("kick"), message.author, reason="Disallowed word/phrase")
                elif config["badWords"][word] == "ban":
                    await ctx.invoke(self.bot.get_command("ban"), message.author, reason="Disallowed word/phrase")
                elif config["badWords"][word] == "report":
                    await moderation_utils.send_report(ctx, message, "Disallowed word/phrase")
                    continue
                else:
                    continue
                await ctx.invoke(self.bot.get_command("report"), message,
                                 reason=f"{moderation_utils.PAST_PARTICIPLES[config['badWords'][word]]} by automod for this message in {ctx.channel.mention}")

    @tasks.loop(minutes=1)
    async def delete_warns(self):
        async for warn in moderation_collection.find({"expired": False}):
            if warn["timestamp"] + (await moderation_utils.get_config())["deleteWarnsAfter"] < time.time():
                await moderation_collection.update_one(warn, {"$set": {"expired": True}})

    @tasks.loop(minutes=1)
    async def timed_punishments(self):
        async for punishment in moderation_collection.find({"active": True, "permanent": False}):
            if punishment["ends"] < time.time():
                await moderation_utils.end_punishment(self.bot, punishment, moderator="automod",
                                                      reason="punishment served")
                await moderation_collection.update_one(punishment, {"$set": {"active": False}})

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await moderation_utils.automod_name(member)
        if await moderation_collection.find_one({"offender_id": member.id, "active": True, "type": "mute"}):
            await member.add_roles(member.guild.get_role((await moderation_utils.get_config())["muteRole"]))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await moderation_utils.automod_name(after)


def setup(bot):
    bot.add_cog(Automod(bot))
