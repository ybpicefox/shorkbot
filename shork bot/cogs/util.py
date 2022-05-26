from discord.ext import commands
import discord
from utils import logic, utils, moderation_utils
from utils.utils import RoleConverter


class Util(commands.Cog, name="Other"):
    def __init__(self, bot, hidden):
        self.hidden = hidden
        self.bot = bot
        self.tags = utils.get_file_json("config/data/tags")

    @commands.command()
    async def rolelist(self, ctx: commands.Context, *, text: str):

        special_tokens = "&|!()"
        tokens = []
        builder = ""
        for char in text:
            if char in special_tokens:
                tokens.append(builder)
                tokens.append(char)
                builder = ""
            else:
                builder += char
        tokens.append(builder)
        empty = []
        for i, item in enumerate(tokens):
            if item == "" or item.isspace():
                empty.append(item)
        for i in empty:
            tokens.remove(i)
        for i, item in enumerate(tokens):
            if item not in special_tokens:
                tokens[i] = await RoleConverter().convert(ctx, item.strip())
        count = 0
        tree = logic.BooleanLogic.OperationBuilder(tokens, lambda item, items: item in items).build()
        async with ctx.typing():
            for member in ctx.guild.members:
                if tree.evaluate(member.roles):
                    count += 1
        embed = discord.Embed(title="Role list search",
                              colour=discord.Colour.blurple()).add_field(name="Query",
                                                                         value=tree.pprint(lambda x: x.mention),
                                                                         inline=False) \
            .add_field(name="Member count", value=f"{count:,}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['commands'])
    async def help(self, ctx: commands.Context, cog: str = None):
        """Displays the help command
        Anything in angled brackets <> is a required argument. Square brackets [] mark an optional argument"""
        prefix = ctx.prefix
        embed: discord.Embed = None
        if not cog:
            embed = discord.Embed(title="Help", description=f"use `{prefix}help [category|command]` for more info",
                                  color=0x00FF00)
            embed.set_footer(text=f"Created by pjones123#6025")
            cog_desc = ''
            for x in self.bot.cogs:
                if not self.bot.cogs[x].hidden:
                    cmd = ''
                    cog_desc += f"__**{x}**__: {self.bot.cogs[x].__doc__}\n"
                    for y in self.bot.get_cog(x).get_commands():
                        if not y.hidden:
                            cmd += f"`{prefix}{y}`,  "
                    embed.add_field(name=f"__**{x}**__: {self.bot.cogs[x].__doc__}", value=cmd, inline=False)
            if not isinstance(ctx.channel, discord.channel.DMChannel):
                await ctx.send("**:mailbox_with_mail: You've got mail**")
            await ctx.author.send(embed=embed)
        else:
            found = False
            cog = cog.lower()
            for x in self.bot.cogs:
                if x.lower() == cog:
                    embed = discord.Embed(title="Help", color=0x00FF00)
                    scog_info = ''
                    for c in self.bot.get_cog(x).get_commands():
                        if not c.hidden:
                            scog_info += f"\n`{prefix}{c.name}`: {c.help}\n"
                    embed.add_field(name=f"\n{cog} Category:\n{self.bot.cogs[cog].__doc__}\n ",
                                    value=f"\n{scog_info}\n", inline=False)
                    found = True

            if not found:
                for x in self.bot.cogs:
                    for c in self.bot.get_cog(x).get_commands():
                        if c.name.lower() == cog:
                            embed = discord.Embed(color=0x00FF00)
                            embed.add_field(name=f"{c.name}: {c.help}",
                                            value=f"Usage:\n `{prefix}{c.qualified_name} {c.signature}`")
                            found = True
            if not found:
                embed = discord.Embed(
                    description="Command not found. Check that you have spelt it correctly and used capitals where appropriate")
            await ctx.author.send(embed=embed)
            if not isinstance(ctx.channel, discord.channel.DMChannel):
                await ctx.send("**:mailbox_with_mail: You've got mail**")

    @commands.command(name="tag")
    async def tag_command(self, ctx: commands.Context, *, tag: str):
        for tag_object in self.tags:
            if tag.lower() == tag_object["name"].lower() or tag.lower() in [z.lower() for z in tag_object["aliases"]]:
                return await ctx.send(tag_object["response"])

    @commands.command()
    async def report(self, ctx, message: discord.Message, *, reason: str = None):
        """Report a message a user has sent"""
        try:
            await ctx.message.delete()
        except:
            pass
        await moderation_utils.send_report(ctx, message, reason)
        try:
            await ctx.author.send(
                "Your report has been submitted. For any further concerns, do not hesitate to contact a staff member")
        except:
            pass


def setup(bot):
    bot.add_cog(Util(bot, False))
