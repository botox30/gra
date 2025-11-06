import datetime
import hikari
import lightbulb
import miru
from miru.ext import menu
from receiptgen import database, utils

plugin = lightbulb.Plugin("get-access")


@plugin.command
@lightbulb.decorators.app_command_permissions(dm_enabled=False)
@lightbulb.command(name="access", description="Your Access Information")
@lightbulb.implements(lightbulb.SlashCommand)
async def get_access(ctx: lightbulb.Context):
    db = database.GuildAPI(guild_id=ctx.guild_id)
    data = await db.get_guild()

    access_role = data.get("access_role", None)
    if access_role is None:
        await ctx.respond("access role was not set up")
        return

    else:
        member_roles = ctx.member.get_roles()
        status = False

        for role in member_roles:
            if role.id == int(access_role):
                status = True


    embed = hikari.Embed(
        title="Access Info",
        color=utils.get_config()["color"],
        timestamp=datetime.datetime.now().astimezone()
    ).add_field(
        "Active", f"`{status}`", inline=True
     ).set_footer(
        text=plugin.bot.get_me().username
    )

    await ctx.respond(embed=embed)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)