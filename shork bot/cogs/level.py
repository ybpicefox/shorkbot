import random

from discord.ext import commands
import discord
import time
import math
import datetime
from EZPaginator import Paginator

from utils import utils
from utils.utils import get_user, Embed, get_file_json, leaderboard_pages, staff_only, save_file_json
from config.bot_secrets import user_collection
import pymongo


class Levelling(commands.Cog, name="levelling"):
    def __init__(self, bot, hidden):
        self.hidden = hidden
        self.bot: commands.Bot = bot
        self.multipliers = {}
        self.global_multiplier = 0
        self.update_multipliers()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.pending and not after.pending:
            level_roles: dict = get_file_json("config/data/level_roles")["levels"]
            roles = []
            user_data = await user_collection.find_one({"_id": str(after.id)})
            if user_data:
                level = user_data["level"]
                for lr in level_roles:
                    if int(lr) > level:
                        break
                    else:
                        roles.append(after.guild.get_role(int(level_roles[str(lr)])))
            await after.add_roles(*roles)

    def update_multipliers(self):
        config: dict = get_file_json("config/data/config")
        self.multipliers = config["multipliers"]
        self.global_multiplier = config["global_multiplier"]

    @commands.command()
    @staff_only
    async def multiplier(self, ctx, channel: discord.TextChannel, value: float):
        """Change the xp multiplier of a channel"""
        if value < -0.5 or value > 10:
            return await ctx.send("Invalid number")
        if value < 0 or value > 10:
            return await ctx.send('resign when')
        config = get_file_json()
        config["multipliers"][str(channel.id)] = value
        await ctx.send(f"Set XP multiplier for {channel.mention} to {value}")
        save_file_json(config)
        self.update_multipliers()

    @commands.command()
    @staff_only
    async def global_multiplier(self, ctx, value: float):
        """Change the global xp multiplier for the whole server"""
        if value < -0.5 or value > 10:
            return await ctx.send("Invalid number")
        config = get_file_json()
        config["global_multiplier"] = value
        await ctx.send(f"Set global XP multiplier to {value}")
        save_file_json(config)
        self.update_multipliers()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.type == discord.MessageType.premium_guild_subscription:
            config = get_file_json()
            config["global_multiplier"] = 2
            save_file_json(config)
            self.update_multipliers()
        if message.author.bot or not message.guild:
            return
        else:
            user_data = await get_user(message.author)
            if str(message.channel.id) in self.multipliers:
                multiplier = self.multipliers[str(message.channel.id)]
            else:
                multiplier = 1
            if message.attachments:
                base_exp = 30
            elif len("".join(message.content)) > 150:
                base_exp = 50
            else:
                base_exp = 25
            base_exp *= 0.1 * random.randint(5, 15)
            exp = math.trunc(multiplier * self.global_multiplier * base_exp)
            if time.time() - user_data["last_message"] > 30:
                points_bonus = 1 if user_data["experience"] > user_data["last_points"] + 1000 else 0
                await user_collection.update_one({"_id": str(message.author.id)},
                                                 {"$inc": {"experience": exp, "weekly": exp, "points": points_bonus},
                                                  "$set": {"last_message": time.time(),
                                                           "last_points": user_data[
                                                                              "experience"] + exp if points_bonus else
                                                           user_data["last_points"]}})
                user_data = await user_collection.find_one({"_id": str(message.author.id)})
            else:
                user_data = await user_collection.find_one({"_id": str(message.author.id)})

            experience = user_data["experience"]
            lvl_start = user_data["level"]
            lvl_end = 50 * (lvl_start ** 1.5)
            if experience > lvl_end:
                await user_collection.update_one({"_id": str(message.author.id)},
                                                 {"$inc": {"level": 1}, "$set": {"experience": 0,
                                                                                 "last_points": 0 - (
                                                                                         experience - (
                                                                                         user_data[
                                                                                             "last_points"] + 100))}})
                await message.channel.send(
                    f":tada: Congrats {message.author.mention}, you levelled up to level {lvl_start + 1}!")
                level_roles = get_file_json("config/data/level_roles")["levels"]
                if str(lvl_start + 1) in level_roles:
                    role = message.guild.get_role(int(level_roles[str(lvl_start + 1)]))
                    await message.author.add_roles(role)

    @commands.command(aliases=['level', "lvl"])
    async def rank(self, ctx, user: discord.Member = None):
        """View your or the mentioned user's level"""
        if not user:
            user = ctx.author
        user_data = await user_collection.find_one({"_id": str(user.id)})
        if not user_data:
            return await ctx.send("This user has no level")
        string = f"XP: {round(user_data['experience']):,}/{round(50 * (round(user_data['level']) ** 1.5)):,}"
        string += f"\nWeekly XP: {round(user_data['weekly']):,}"
        string += f"\nPoints: {user_data['points']:,}"
        string += f"\nTotal XP: {(sum([round(50 * z ** 1.5) for z in range(1, user_data['level'])]) + user_data['experience']):,}"
        embed = Embed(user, title=f"Level: {str(round(user_data['level']))}",
                      description=string).auto_author()
        await ctx.send(embed=embed)

    @commands.command(name="howFarFromLevel", aliases=["hffl"])
    async def how_far_from_level(self, ctx, wanted_level: int):
        '''View how far from a specific level you are, along with some other information'''
        user = ctx.author
        user_data = await user_collection.find_one({"_id": str(user.id)})
        level = user_data['level']
        xp = user_data['experience']
        if wanted_level <= level or wanted_level > 500:
            await ctx.send("This number is invalid")
        else:
            def total_xp(y):
                return sum([round(50 * z ** 1.5) for z in range(1, y)])

            def level_xp(x):
                return round(50 * (x ** 1.5))

            embed: discord.Embed = discord.Embed(title="XP Calculator")
            embed.add_field(name="Desired Level",
                            value=f"XP until desired level: {(sum([round(50 * z ** 1.5) for z in range(level, wanted_level)]) - xp):,}\nXP of desired level: {(level_xp(wanted_level)):,}")
            embed.add_field(name="Total XP Stats",
                            value=f"Total XP of desired level: {(total_xp(wanted_level)):,}\nYour total XP: {(total_xp(level) + xp):,}",
                            inline=False)
            embed.add_field(name="Next Level",
                            value=f"XP until next level: {(level_xp(level) - xp):,}\nXP of next level: {(level_xp(level + 1)):,}",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.command(aliases=["lb"])
    @commands.guild_only()
    async def leaderboard(self, ctx):
        """View the server's XP leaderboard"""
        embeds = leaderboard_pages(self.bot, ctx.guild,
                                   [z async for z in user_collection.find({}).sort('level', pymongo.DESCENDING)],
                                   prefix="level ")
        message = await ctx.send(embed=embeds[0])
        await Paginator(self.bot, message, embeds=embeds, timeout=60, use_extend=True, only=ctx.author).start()

    @commands.command(aliases=["wk"])
    @commands.guild_only()
    async def weekly(self, ctx):
        """View the server's weekly XP leaderboard"""
        embeds = leaderboard_pages(self.bot, ctx.guild, [z async for z in user_collection.find({}).sort('weekly', pymongo.DESCENDING)], key="weekly", suffix=" XP")
        msg = await ctx.send(embed=embeds[0])
        await Paginator(self.bot, msg, embeds=embeds, timeout=60, use_extend=True, only=ctx.author).start()

    @commands.command(name="levelBackup", hidden=True)
    @staff_only
    async def level_backup(self, ctx):
        users = {}
        async for user in user_collection.find({}):
            users[str(user["_id"])] = user
        save_file_json(users, f"data/backups/{datetime.datetime.now().strftime('%d%m%y')}.json")
        await ctx.send("Backup created")

    @commands.command(name="removeXP", hidden=True)
    @staff_only
    async def remove_xp(self, ctx: commands.Context, user: discord.Member, xp: int):
        """Remove xp from someone"""
        new_ctx = ctx
        # noinspection PyPropertyAccess
        new_ctx.author = user
        if utils.staff_check(new_ctx):
            return await ctx.send("Cannot remove XP from that user")
        if xp < 0:
            return await ctx.send("Invalid number")
        if (await user_collection.find_one({"_id": str(user.id)}))["experience"] < xp:
            await user_collection.update_one({"_id": str(user.id)}, {"$set": {"experience": 0}})
        else:
            await user_collection.update_one({"_id": str(user.id)}, {"$inc": {"experience": -xp}})
        await ctx.send(f"removed {xp} xp from {user.mention}")


def setup(bot):
    bot.add_cog(Levelling(bot, False))
