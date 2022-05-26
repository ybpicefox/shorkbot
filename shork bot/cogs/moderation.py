from discord.ext import commands
import typing
from utils.utils import TimeConverter, staff_only, MemberUserConverter
import discord
from utils import payloads, moderation_utils
from config.bot_secrets import moderation_collection
import datetime
from EZPaginator import Paginator


class Moderation(commands.Cog, name="Moderation"):  # moderation commands, warns, mutes etc.
    def __init__(self, bot, hidden):
        self.hidden = hidden
        self.bot = bot

    @commands.command()
    @staff_only
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """Give a user a warning"""
        payload = payloads.warn_payload(offender_id=user.id, mod_id=ctx.author.id, reason=reason)
        message = await ctx.send(embed=moderation_utils.chat_embed(ctx, payload))
        payload = payloads.insert_message(payload, message)
        await moderation_collection.insert_one(payload)
        await user.send(f"You were warned in {ctx.guild.name} for {reason}\nInfraction ID:`{payload['id']}`")
        await moderation_utils.log(self.bot, payload)
        await moderation_utils.warn_punishments(ctx, user)

    @commands.command()
    @staff_only
    async def mute(self, ctx, user: discord.Member, _time: typing.Optional[TimeConverter] = None, *,
                   reason: str = "none"):
        """Mute a user"""
        if user.guild_permissions.manage_messages:
            return await ctx.send("You cannot mute a moderator/administrator")
        payload = payloads.mute_payload(offender_id=user.id, mod_id=ctx.author.id, duration=_time, reason=reason)
        message = await ctx.send(embed=moderation_utils.chat_embed(ctx, payload))
        payload = payloads.insert_message(payload, message)
        await user.add_roles(ctx.guild.get_role((await moderation_utils.get_config())["muteRole"]), reason=f"mod: {ctx.author} | reason: {reason[:400]}{'...' if len(reason) > 400 else ''}")
        await moderation_collection.insert_one(payload)
        await moderation_utils.log(self.bot, payload)
        time_string = payload["duration_string"]
        await user.send(
            f"You were muted in {ctx.guild.name} {f'for `{time_string}`' if _time else ''} {f'for `{reason}`' if reason else ''}\nInfraction ID:`{payload['id']}`")

    @commands.command()
    @staff_only
    async def unmute(self, ctx, user: discord.Member, *, reason: str = "none"):
        """Unmute a user"""
        await moderation_collection.delete_many({"offender_id": user.id, "type": "mute"})
        await user.remove_roles(ctx.guild.get_role((await moderation_utils.get_config())["muteRole"]), reason=f"mod: {ctx.author} | reason: {reason[:400]}{'...' if len(reason) > 400 else ''}")
        await moderation_utils.end_log(self.bot, {"type": "mute", "offender_id": user.id}, moderator=ctx.author,
                                       reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Unmuted {user}", colour=discord.Colour.green()))

    @commands.command()
    @staff_only
    async def ban(self, ctx, user: MemberUserConverter, _time: typing.Optional[TimeConverter]=None, *, reason: str = "none"):
        """Ban a user"""
        if isinstance(user, discord.Member):
            if user.guild_permissions.manage_messages:
                return await ctx.send("You cannot ban a moderator/administrator")
        payload = payloads.ban_payload(offender_id=user.id, mod_id=ctx.author.id, duration=_time, reason=reason)
        message = await ctx.send(embed=moderation_utils.chat_embed(ctx, payload))
        payload = payloads.insert_message(payload, message)
        time_string = payload["duration_string"]
        try:
            await user.send(
                f"You were banned from {ctx.guild.name} {f'for `{time_string}`' if _time else ''} {f'for `{reason}`' if reason else ''}\nInfraction ID:`{payload['id']}`")
        except discord.Forbidden:
            pass
        await ctx.guild.ban(user, reason=f"mod: {ctx.author} | reason: {reason[:400]}{'...' if len(reason) > 400 else ''}")
        await moderation_collection.insert_one(payload)
        await moderation_utils.log(self.bot, payload)

    @commands.command()
    @staff_only
    async def unban(self, ctx, member, *, reason: str = "none"):
        """Unban a user"""
        try:
            await ctx.guild.unban(moderation_utils.BannedUser(member), reason=f"mod: {ctx.author} | reason: {reason[:400]}{'...' if len(reason) > 400 else ''}")
        except (discord.NotFound, discord.HTTPException):
            return await ctx.send("Could not find a ban for that user")
        await moderation_utils.end_log(self.bot, {"type": "ban", "offender_id": member}, moderator=ctx.author,
                                       reason=reason)
        await ctx.send(embed=discord.Embed(description=f"**{member} was unbanned**", color=discord.Colour.green()))

    @commands.command()
    @staff_only
    async def delwarn(self, ctx, _id: str):
        """Delete a warning from someone"""
        doc = await moderation_collection.find_one({"id": _id})
        if not doc:
            return await ctx.send("Could not find that warning")
        else:
            await moderation_collection.update_one(doc, {"$set": {"expired": True}})
            await ctx.send("Successfully deleted warning `{}`".format(_id))

    @commands.command()
    @staff_only
    async def kick(self, ctx, user: discord.Member, *, reason: str = "none"):
        """Kick a user"""
        if user.guild_permissions.manage_messages:
            embed = discord.Embed(description="You cannot kick a moderator/administrator", color=0xff0000)
            return await ctx.send(embed=embed)
        payload = payloads.kick_payload(offender_id=user.id, mod_id=ctx.author.id, reason=reason)
        message = await ctx.send(embed=moderation_utils.chat_embed(ctx, payload))
        payload = payloads.insert_message(payload, message)
        await moderation_collection.insert_one(payload)
        await moderation_utils.log(self.bot, payload)
        try:
            await user.send(
                f"You were kicked from {ctx.guild.name} {f'for `{reason}`' if reason else 'No reason given'}\nInfraction ID:`{payload['id']}`")
        except discord.Forbidden:
            pass
        await user.kick(reason=f"mod: {ctx.author} | reason: {reason[:400]}{'...' if len(reason) > 400 else ''}")

    @commands.command()
    @staff_only
    async def punishments(self, ctx, user: MemberUserConverter = None):
        """View a user's punishments"""
        user = user if user else ctx.author
        warnings = [z async for z in moderation_collection.find({"offender_id": user.id, "expired": False})]
        embed = discord.Embed(title=f"{len(warnings)} punishments", colour=discord.Colour.green())
        embed.set_author(name=user, icon_url=user.avatar_url)
        for warning in warnings:
            embed.add_field(name=f"ID: {warning['id']} | {self.bot.get_user(warning['mod_id'])}",
                            value=f"[{warning['type']}] {warning['reason']} - {datetime.datetime.fromtimestamp(warning['timestamp']).strftime('%d/%m/%Y, %H:%M:%S')}",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def warnings(self, ctx, user: MemberUserConverter = None):
        """View a user's warnings"""
        user = user if user else ctx.author
        warnings = [z async for z in moderation_collection.find({"offender_id": user.id, "expired": False, "type": "warn"})]
        embed = discord.Embed(title=f"{len(warnings)} warnings", colour=discord.Colour.green())
        embed.set_author(name=user, icon_url=user.avatar_url)
        for warning in warnings:
            embed.add_field(name=f"ID: {warning['id']} | {self.bot.get_user(warning['mod_id'])}",
                            value=f"{warning['reason']} - {datetime.datetime.fromtimestamp(warning['timestamp']).strftime('%d/%m/%Y, %H:%M:%S')}",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @staff_only
    async def modlogs(self, ctx, user: MemberUserConverter):
        """View all of a user's moderation logs"""
        user = user if user else ctx.author
        infractions = [z async for z in moderation_collection.find({"offender_id": user.id})]
        if not infractions:
            return await ctx.send(f"No infractions found for {user}")
        embeds = [discord.Embed(title=f"All infractions for {user}", color=discord.Colour.orange())]
        embed_count = 0
        for i, infraction in enumerate(infractions):
            embeds[embed_count].add_field(
                name=f"{infraction['type']} | ID: {infraction['id']} | {self.bot.get_user(infraction['mod_id'])}",
                value=f"{infraction['reason']} - {datetime.datetime.fromtimestamp(infraction['timestamp']).strftime('%d/%m/%Y, %H:%M:%S')}",
                inline=False)
            if not i % 5 and i != 0:
                embed_count += 1
                embeds.append(discord.Embed(title=f"All infractions for {user}", color=discord.Colour.orange()))
        msg = await ctx.send(embed=embeds[0])
        if len(embeds) == 1:
            return
        for i, e in enumerate(embeds):
            e.set_footer(text=f"page {i+1} of {len(embeds)}")
        pages = Paginator(self.bot, msg, embeds=embeds, timeout=60, use_extend=True, only=ctx.author)
        await pages.start()
                
    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def whereiswarn(self, ctx, warn: str):
        """Find where someone was warned"""
        warning = await moderation_collection.find_one({"id": warn})
        if not warning:
            return await ctx.send("Could not find a warning with that ID")
        location = warning["message"].split('-')
        await ctx.send(f"https://discord.com/channels/{location[0]}/{location[1]}/{location[2]}")

    async def cog_after_invoke(self, ctx):
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Moderation(bot, True))
