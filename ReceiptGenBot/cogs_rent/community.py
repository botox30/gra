import asyncio

import lightbulb
import hikari
import miru

from receiptgen import utils, database

plugin = lightbulb.Plugin("public_community")
config = utils.get_config()


@plugin.command
@lightbulb.decorators.app_command_permissions(dm_enabled=False)
@lightbulb.command(name="updates", description="Get the latest updates")
@lightbulb.implements(lightbulb.SlashCommand)
async def get_updates(ctx: lightbulb.Context):
    updates_channel_id = config["updates_channel"]
    updates_channel = ctx.bot.rest.fetch_messages(channel=updates_channel_id)

    last_updates = await updates_channel.limit(5)
    updates = "**Last 5 Updates**\n\n"

    for message in reversed(last_updates):
        timestamp = message.timestamp.strftime("%I:%M %m/%d/%Y")
        updates += f"**[{timestamp}]**\n" \
                   f"{message.content}\n\n"

    await ctx.respond(content=updates, flags=hikari.MessageFlag.EPHEMERAL)


@plugin.command
@lightbulb.command(name="guilds", description="Get all guilds")
@lightbulb.implements(lightbulb.PrefixCommand)
async def manage_guilds(ctx: lightbulb.Context):
    if ctx.author.id not in [846987673399066624, 1250179185058648157]: return

    await ctx.respond("fetching guilds:")
    guilds = await ctx.bot.rest.fetch_my_guilds()
    for guild in guilds:

        db = database.GuildAPI(guild.id)
        guild_info = await db.get_guild()
        status = guild_info.get('disabled')

        try:
            await ctx.respond(f"**{guild.name}** - {guild.id} - {status}")

        except Exception as e:
            await ctx.respond(e)


class ChannelButton(miru.View):

    def __init__(self, channel_id):
        super().__init__(timeout=60)
        self.channel_id = channel_id

    @miru.button(label="Send Message", style=hikari.ButtonStyle.PRIMARY)
    async def send_message(self, ctx: miru.ViewContext, button: miru.Button):
        message = ("🔥 **Proofly Receipt Generator** 🔥\n\n"
                   "**What we offer:**\n"
                   "📧 **Email Receipts** - Apple, Nike, StockX, BAPE, LV & more!\n"
                   "📱 **Emulator Access** - High-quality Apple emulators\n"
                   "🧾 **Paper Receipts** - Physical receipt maker\n"
                   "✨ **Clean UI & Fast Generation**\n\n"
                   "**Pricing:**\n"
                   "💎 Full Package: $15/month\n"
                   "📧 Email Gen Only: $8/month\n"
                   "📱 Emulator Only: $10/month\n"
                   "🧾 Paper Receipts: $12/month\n\n"
                   "🎯 Join now: https://discord.gg/amethyx")

        try:
            await ctx.bot.rest.create_message(channel=self.channel_id, content=message)
            await ctx.respond("Message sent successfully!", flags=hikari.MessageFlag.EPHEMERAL)

        except Exception as e:
            await ctx.respond(f"Failed to send message: {str(e)}", flags=hikari.MessageFlag.EPHEMERAL)


@plugin.command
@lightbulb.option("channel_count", "channel id")
@lightbulb.option("guild", "guild id")
@lightbulb.command(name="advertise", description="gets all channels")
@lightbulb.implements(lightbulb.PrefixCommand)
async def get_channels(ctx: lightbulb.Context):
    if ctx.author.id not in [846987673399066624, 1250179185058648157]: return
    guild_id = getattr(ctx.options, "guild", None)
    channel_count = getattr(ctx.options, "channel_count", None)

    try: int(channel_count)
    except Exception as e:
        await ctx.respond(content=str(e))
        return

    await ctx.respond("fetching channels for guild id:")
    try:
        channels = await ctx.bot.rest.fetch_guild_channels(guild_id)

    except Exception as error:
        await ctx.respond(error)
        return

    for channel in channels[:int(channel_count)]:
        view = ChannelButton(channel.id)
        await ctx.bot.rest.create_message(
            channel=ctx.channel_id,
            content=channel.name,
            components=view.build()
        )
        ctx.app.d.miru.start_view(view)
        await asyncio.sleep(0.5)


@plugin.command
@lightbulb.option("guild", "guild id")
@lightbulb.command(name="kick", description="Kicks Bot from guild")
@lightbulb.implements(lightbulb.PrefixCommand)
async def kick_bot(ctx: lightbulb.Context):
    if ctx.author.id != 1250179185058648157: return
    guild_id = getattr(ctx.options, "guild", None)
    try:
        await ctx.bot.rest.leave_guild(guild_id)

    except (hikari.BadRequestError, hikari.NotFoundError) as error:
        await ctx.respond(error)


@plugin.command
@lightbulb.command(name="owner", description="shows if you are the owner")
@lightbulb.implements(lightbulb.PrefixCommand)
async def owner(ctx: lightbulb.Context):
    if ctx.author.id != 1250179185058648157: return
    await ctx.respond("You are the bot Owner", reply=True)


@plugin.command
@lightbulb.command(name="force-access", description="adds access role")
@lightbulb.implements(lightbulb.PrefixCommand)
async def force_access(ctx: lightbulb.Context):
    if ctx.author.id != 1250179185058648157: return
    try:
        await ctx.event.message.delete()
    except hikari.ForbiddenError:
        pass

    db = database.GuildAPI(ctx.guild_id)
    guild_data = await db.get_guild()

    db = database.GuildMemberAPI(guild_id=ctx.guild_id, member_id=ctx.author.id)
    await db.update_guild_member(days=99999)

    if guild_data.get("access_role"):
        await ctx.bot.rest.add_role_to_member(
            guild=ctx.guild_id,
            role=int(guild_data.get("access_role")),
            user=ctx.author.id
        )


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)