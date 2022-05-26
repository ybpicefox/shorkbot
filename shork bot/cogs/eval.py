import os
import sys
from inspect import getsource
from time import time
from discord.ext import commands
import discord


def prepare(string):
    arr = string.strip("```").replace("py\n", "").replace("python\n", "").split("\n")
    if not arr[::-1][0].replace(" ", "").startswith("return"):
        arr[len(arr) - 1] = "return " + arr[::-1][0]
    return "".join(f"\n\t{i}" for i in arr)


def resolve_variable(variable):
    if hasattr(variable, "__iter__"):
        var_length = len(list(variable))
        if (var_length > 100) and (not isinstance(variable, str)):
            return f"<a {type(variable).__name__} iterable with more than 100 values ({var_length})>"
        elif not var_length:
            return f"<an empty {type(variable).__name__} iterable>"

    if (not variable) and (not isinstance(variable, bool)):
        return f"<an empty {type(variable).__name__} object>"
    return variable if (len(f"{variable}") <= 1000) else f"<a long {type(variable).__name__} object with the " \
                                                         f"length of {len(f'{variable}'):,}> "


class EvalCommand(commands.Cog, name="EvalCommand"):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True

    @commands.command(pass_context=True, aliases=['-eval', '-exec', '-evaluate'])
    @commands.has_any_role(826442145275183135, 855679399810433054)
    async def _eval(self, ctx, *, code: str):
        silent = ("-s" in code)

        code = prepare(code.replace("-s", ""))
        args = {
            "discord": discord,
            "sauce": getsource,
            "sys": sys,
            "os": os,
            "imp": __import__,
            "this": self,
            "ctx": ctx
        }

        try:
            exec(f"async def func():{code}", args)
            a = time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(response, discord.Message):
                del args, code
                return

            await ctx.send(
                f"```py\n{resolve_variable(response)}````{type(response).__name__} | {(time() - a) / 1000} ms`")
        except Exception as e:
            await ctx.send(f"Error occurred:```\n{type(e).__name__}: {str(e)}```")

        del args, code, silent


def setup(bot):
    bot.add_cog(EvalCommand(bot))
