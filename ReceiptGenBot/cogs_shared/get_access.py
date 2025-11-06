import datetime
import hikari
import lightbulb
import miru
import json
import os

from miru.ext import menu
from receiptgen import database, utils

plugin = lightbulb.Plugin("get-access")


class ManualSubscriptionManager:
    """
    Manages user subscriptions stored in a JSON file.
    """
    _file_path = "manual_subscriptions.json"

    def __init__(self):
        self._load_data()

    def _load_data(self):
        """Loads subscription data from the JSON file."""
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r") as f:
                    self._subscriptions = json.load(f)
            except json.JSONDecodeError:
                print("Error decoding manual_subscriptions.json. Using an empty dictionary.")
                self._subscriptions = {}
        else:
            self._subscriptions = {}

    def _save_data(self):
        """Saves subscription data to the JSON file."""
        with open(self._file_path, "w") as f:
            json.dump(self._subscriptions, f, indent=4)

    def get_subscription(self, user_id: int) -> dict | None:
        """Retrieves subscription data for a given user ID."""
        user_id_str = str(user_id)
        return self._subscriptions.get(user_id_str)

    def set_subscription(self, user_id: int, is_active: bool, end_date: str | None, is_forever: bool = False):
        """Sets or updates subscription data for a user."""
        user_id_str = str(user_id)
        self._subscriptions[user_id_str] = {
            "is_active": is_active,
            "end_date": end_date,
            "is_forever": is_forever
        }
        self._save_data()

    def delete_subscription(self, user_id: int):
        """Deletes subscription data for a user."""
        user_id_str = str(user_id)
        if user_id_str in self._subscriptions:
            del self._subscriptions[user_id_str]
            self._save_data()


@plugin.command
@lightbulb.decorators.app_command_permissions(dm_enabled=False)
@lightbulb.command(name="access", description="Your Access Information")
@lightbulb.implements(lightbulb.SlashCommand)
async def get_access(ctx: lightbulb.Context):
    db = database.GuildMemberAPI(guild_id=ctx.guild_id, member_id=ctx.author.id)
    try:
        data = await db.get_guild_member()
    except Exception as e:
        await ctx.respond("Database connection error. Please try again later.", flags=hikari.MessageFlag.EPHEMERAL)
        return

    access = data.get("has_access", False)
    access_end = data.get("access_end")

    if access_end:
        try:
            access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            try:
                access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S")

    embed = hikari.Embed(
        title="Access Info",
        color=utils.get_config()["color"],
        timestamp=datetime.datetime.now().astimezone()
    ).add_field("Till", "`None`", inline=True) \
        .add_field("Ends", "`None`", inline=True) \
        .add_field("Active", "`False`", inline=True) \
        .set_footer(text=plugin.bot.get_me().username)

    if not access and access_end:
        embed = hikari.Embed(
            title="Access Info",
            timestamp=datetime.datetime.now().astimezone()
           ).add_field("Till", "`None`", inline=True) \
            .add_field("Ended", f"<t:{int(access_end.timestamp())}:R>", inline=True) \
            .add_field("Active", "`False`", inline=True) \
            .set_footer(text=plugin.bot.get_me().username)

    if not access:
        await ctx.respond(embed=embed)
        return

    access_end_naive = access_end.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    remaining_time = access_end_naive - datetime.datetime.utcnow()

    till = f"<t:{int(access_end.timestamp())}:D>"
    ends = f"<t:{int(access_end.timestamp())}:R>"

    if remaining_time.days >= 999:
        till = "`None`"
        ends = "`Never`"

    embed = hikari.Embed(
        title="Access Info",
        color=utils.get_config()["color"],
        timestamp=datetime.datetime.now().astimezone()
    ).add_field("Till", till, inline=True)\
     .add_field("Ends", ends, inline=True)\
     .add_field("Active", f"`{access}`", inline=True)\
     .set_footer(text=plugin.bot.get_me().username)

    await ctx.respond(embed=embed)


@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option("member", "Discord User", required=True, type=hikari.Member)
@lightbulb.command(name="get_user_access", description="Get User Access")
@lightbulb.implements(lightbulb.SlashCommand)
async def get_user_access(ctx: lightbulb.Context):
    member = getattr(ctx.options, "member", None)

    # Get member data from database
    member_db = database.GuildMemberAPI(guild_id=ctx.guild_id, member_id=member.id)
    try:
        member_data = await member_db.get_guild_member()
    except Exception as e:
        await ctx.respond("Database connection error. Please try again later.", flags=hikari.MessageFlag.EPHEMERAL)
        return

    # Check manual subscription as backup/override
    manual_sub = ManualSubscriptionManager()
    manual_data = manual_sub.get_subscription(member.id)

    if manual_data:
        print(f"DEBUG: Manual subscription found: {manual_data}")
        # Override database data with manual data if manual subscription exists
        if manual_data.get("is_forever"):
            access = True
            access_end = None
        else:
            access = manual_data.get("is_active", False)
            access_end = manual_data.get("end_date")

        print(f"DEBUG: Using manual subscription data - access: {access}, end: {access_end}")
    else:
        access = member_data.get("has_access", False)
        access_end = member_data.get("access_end")
        
        print(f"DEBUG: Using database data - access: {access}, end: {access_end}")

    # Parse access_end if it exists
    parsed_access_end = None
    if access_end:
        print(f"DEBUG: Parsing access_end: {access_end}")
        try:
            # Try timezone-naive format with microseconds first (most common from your database)
            parsed_access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S.%f")
            print(f"DEBUG: Parsed as timezone-naive with microseconds: {parsed_access_end}")
        except ValueError:
            try:
                # Try timezone-naive format without microseconds
                parsed_access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S")
                print(f"DEBUG: Parsed as timezone-naive without microseconds: {parsed_access_end}")
            except ValueError:
                try:
                    # Try timezone-aware format with microseconds
                    parsed_access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S.%f%z")
                    print(f"DEBUG: Parsed as timezone-aware with microseconds: {parsed_access_end}")
                except ValueError:
                    try:
                        # Try timezone-aware format without microseconds
                        parsed_access_end = datetime.datetime.strptime(access_end, "%Y-%m-%dT%H:%M:%S%z")
                        print(f"DEBUG: Parsed as timezone-aware without microseconds: {parsed_access_end}")
                    except ValueError:
                        print(f"DEBUG: Failed to parse access_end: {access_end}")
                        parsed_access_end = None

    # Determine the actual status based on access flag and expiration
    is_active = False
    till_text = "`None`"
    ends_text = "`None`"

    print(f"DEBUG: Processing status - access: {access}, parsed_access_end: {parsed_access_end}")

    # If there's an access_end date, check if it's in the future
    if parsed_access_end:
        current_time = datetime.datetime.utcnow()
        
        # Handle timezone-naive datetime from database
        if parsed_access_end.tzinfo is None:
            # Assume database times are in UTC if no timezone info
            access_end_utc = parsed_access_end
        else:
            # Convert timezone-aware datetime to UTC
            access_end_utc = parsed_access_end.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        
        print(f"DEBUG: Current time: {current_time}, Access end UTC: {access_end_utc}")

        if access_end_utc > current_time:
            # Access is valid and not expired
            is_active = True
            remaining_time = access_end_utc - current_time
            
            print(f"DEBUG: Access is active, remaining days: {remaining_time.days}")

            if remaining_time.days >= 999:
                till_text = "`Forever`"
                ends_text = "`Never`"
            else:
                till_text = f"<t:{int(parsed_access_end.timestamp())}:D>"
                ends_text = f"<t:{int(parsed_access_end.timestamp())}:R>"
                print(f"DEBUG: Set till_text: {till_text}, ends_text: {ends_text}")
        else:
            # Access expired
            is_active = False
            till_text = "`None`"
            ends_text = f"<t:{int(parsed_access_end.timestamp())}:R>"
            print(f"DEBUG: Access expired")
    elif access:
        # User has access but no end date - this should only happen for forever access or manual roles
        print(f"DEBUG: User has access but no end date")
        
        # Check if this is from manual subscription file
        if manual_data and manual_data.get("is_forever"):
            is_active = True
            till_text = "`Forever`"
            ends_text = "`Never`"
            print(f"DEBUG: Manual forever access detected")
        # Check if this is from database with forever access (no access_end means forever in database)
        elif member_data.get("has_access") and not member_data.get("access_end"):
            is_active = True
            till_text = "`Forever`"
            ends_text = "`Never`"
            print(f"DEBUG: Database forever access detected")
        
    else:
        # User doesn't have access and no end date
        is_active = False
        till_text = "`None`"
        ends_text = "`None`"
        print(f"DEBUG: No access detected")

    # Create embed based on status
    embed = hikari.Embed(
        title="Subscription Info",
        description=f"user: {member.mention}",
        color=utils.get_config()["color"],
        timestamp=datetime.datetime.now().astimezone()
    ).add_field("Till", till_text, inline=True) \
        .add_field("Ends" if is_active else ("Ended" if parsed_access_end else "Ends"), ends_text, inline=True) \
        .add_field("Active", f"`{is_active}`", inline=True) \
        .set_footer(text=plugin.bot.get_me().username)

    await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)