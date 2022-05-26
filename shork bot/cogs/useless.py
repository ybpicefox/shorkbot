import sys

import discord
from discord.ext import commands
import random
import datetime
import asyncio

from utils.utils import staff_only


class Useless(commands.Cog, name='Random'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.command()
    async def smh(self, ctx):
        embed = discord.Embed(colour=discord.Colour.blurple(), description=f"{ctx.author.mention} shakes their head")
        await ctx.send(embed=embed)

    @commands.command()
    async def f(self, ctx):
        embed = discord.Embed(colour=discord.Colour.blurple(),
                              description=f"<:pressf:855745349537103884>{ctx.author.mention} has paid their respects")
        await ctx.send(embed=embed)

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx):
        responses_list = ['Yes.', 'No.', 'Maybe.', 'Definitely', 'Not at all.', 'Ask me another time.']
        choice = random.choice(responses_list)
        embed = discord.Embed(color=0xFFFFFF)
        embed.set_author(name=' 8ball ')
        embed.add_field(name=":8ball: 8Ball Says...", value=f'`{choice}`')
        await ctx.send(embed=embed)

    @commands.command()
    async def hug(self, ctx, user: discord.User):
        embed = discord.Embed(colour=discord.Colour.blurple(),
                              description=f"<:hug:855742434725855232>{ctx.author.mention} hugged {user.mention}")
        await ctx.send(embed=embed)

    @commands.command(name='bot', aliases=['info', 'botinfo'])
    async def _bot(self, ctx):
        embed = discord.Embed(title='Bot Information',
                              description='Created by pjones123#6025 and other stuff by Lightning#1010 and mrlobaker#2037',
                              color=0xff003d)

        embed.set_thumbnail(
            url='https://images-ext-2.discordapp.net/external/gf8sjTwr0DCWMKpYuNd8yXlzvywht43aRWh6QjnMPw0/%3Fsize%3D128/https/cdn.discordapp.com/avatars/648362865048420373/bf8b2c1ed038e8d19f8863db3fba526c.png')
        embed.set_footer(text='Leveling',
                         icon_url='https://images-ext-2.discordapp.net/external/gf8sjTwr0DCWMKpYuNd8yXlzvywht43aRWh6QjnMPw0/%3Fsize%3D128/https/cdn.discordapp.com/avatars/648362865048420373/bf8b2c1ed038e8d19f8863db3fba526c.png')

        embed.add_field(name='**Total Guilds**', value=f'`{len(list(self.bot.guilds))}`', inline=True)
        embed.add_field(name='**Total Users**', value=f'`{len(list(self.bot.users))}`', inline=True)
        text = len([*filter(lambda c: isinstance(c, discord.TextChannel), self.bot.get_all_channels())])
        embed.add_field(name='**Total Channels**', value=f'`{text}`', inline=True)
        v = sys.version_info
        embed.add_field(name='**Python Version**', value=f'`{v.major}.{v.minor}.{v.micro}`', inline=True)
        embed.add_field(name='**Discord.py Version**', value=f'`{discord.__version__}`', inline=True)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command()
    async def stab(self, ctx, user: discord.User):
        if ctx.author == user:
            embed = discord.Embed(colour=discord.Colour.blurple(),
                                  description=f"{ctx.author.mention}, please don't do self-harm.")
        else:
            embed = discord.Embed(colour=discord.Colour.blurple(),
                                  description=f"{ctx.author.mention} stabbed {user.mention}")
        await ctx.send(embed=embed)

    @commands.command(aliases=['gn'])
    async def goodnight(self, ctx, user: discord.User):
        embed = discord.Embed(colour=discord.Colour.blurple(),
                              description=f"{ctx.author.mention} says goodnight to {user.mention}")
        await ctx.send(embed=embed)

    @commands.command()
    @staff_only
    async def botlock(self, ctx: commands.Context):
        overwrites = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites.read_messages, overwrites.send_messages = False, False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        overwrites = ctx.channel.overwrites_for(ctx.me)
        overwrites.send_messages, overwrites.read_messages = True, True
        await ctx.channel.set_permissions(ctx.me, overwrite=overwrites)

    @commands.command()
    @staff_only
    async def botunlock(self, ctx: commands.Context):
        overwrites = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites.read_messages, overwrites.send_messages = True, True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        overwrites = ctx.channel.overwrites_for(ctx.me)
        overwrites.send_messages, overwrites.read_messages = True, True
        await ctx.channel.set_permissions(ctx.me, overwrite=overwrites)

    @commands.command()
    @staff_only
    async def lock(self, ctx: commands.Context):
        overwrites = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        overwrites = ctx.channel.overwrites_for(ctx.me)
        overwrites.send_messages, overwrites.read_messages = True, True
        await ctx.channel.set_permissions(ctx.me, overwrite=overwrites)

    @commands.command()
    @staff_only
    async def unlock(self, ctx: commands.Context):
        overwrites = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        overwrites = ctx.channel.overwrites_for(ctx.me)
        overwrites.send_messages, overwrites.read_messages = True, True
        await ctx.channel.set_permissions(ctx.me, overwrite=overwrites)
        
    @commands.command()
    @staff_only
    async def color(self, ctx):
        message = await ctx.send("<:Green_Pastel:845923174730563614> <:Pink_Pastel:845923174674726912>")
        await asyncio.sleep(0)
        await message.edit(content="<:Pink_Pastel:845923174674726912> <:Green_Pastel:845923174730563614>")


def setup(bot):
    bot.add_cog(Useless(bot))
