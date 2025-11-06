
import lightbulb
import hikari
from receiptgen.subscription_manager import ManualSubscriptionManager
from receiptgen import utils
import datetime

plugin = lightbulb.Plugin("manual_sub")

@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option("days", "Number of days (leave empty for forever)", type=int, required=False)
@lightbulb.option("member", "Member to give access", type=hikari.Member)
@lightbulb.command("manual_add", "Manually add subscription via file")
@lightbulb.implements(lightbulb.SlashCommand)
async def manual_add_access(ctx: lightbulb.Context):
    member = ctx.options.member
    days = ctx.options.days
    
    manual_sub = ManualSubscriptionManager()
    result = manual_sub.add_subscription(
        user_id=member.id,
        days=days,
        guild_id=ctx.guild_id
    )
    
    duration_text = f"{days} days" if days else "forever"
    
    embed = hikari.Embed(
        title="Manual Subscription Added",
        description=f"Added {duration_text} access to {member.mention} via manual file",
        color=utils.get_config()["color"],
        timestamp=datetime.datetime.now().astimezone()
    ).add_field("User ID", str(member.id), inline=True) \
     .add_field("Duration", duration_text, inline=True) \
     .add_field("End Date", result.get("end_date", "Never"), inline=True)
    
    await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)

@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option("member", "Member to remove access", type=hikari.Member)
@lightbulb.command("manual_remove", "Manually remove subscription via file")
@lightbulb.implements(lightbulb.SlashCommand)
async def manual_remove_access(ctx: lightbulb.Context):
    member = ctx.options.member
    
    manual_sub = ManualSubscriptionManager()
    success = manual_sub.remove_subscription(member.id)
    
    if success:
        embed = hikari.Embed(
            title="Manual Subscription Removed",
            description=f"Removed manual subscription for {member.mention}",
            color="#ff244c",
            timestamp=datetime.datetime.now().astimezone()
        )
    else:
        embed = hikari.Embed(
            title="Manual Subscription Not Found",
            description=f"No manual subscription found for {member.mention}",
            color="#ff244c",
            timestamp=datetime.datetime.now().astimezone()
        )
    
    await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)

@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.command("manual_list", "List all manual subscriptions")
@lightbulb.implements(lightbulb.SlashCommand)
async def manual_list_subscriptions(ctx: lightbulb.Context):
    manual_sub = ManualSubscriptionManager()
    active_subs = manual_sub.get_active_subscriptions()
    
    if not active_subs:
        embed = hikari.Embed(
            title="Manual Subscriptions",
            description="No active manual subscriptions found",
            color=utils.get_config()["color"]
        )
    else:
        embed = hikari.Embed(
            title="Active Manual Subscriptions",
            description=f"Found {len(active_subs)} active subscriptions",
            color=utils.get_config()["color"],
            timestamp=datetime.datetime.now().astimezone()
        )
        
        for user_id, sub in list(active_subs.items())[:10]:  # Limit to 10 to avoid embed limits
            duration = "Forever" if sub.get("is_forever") else f"{sub.get('days', 'Unknown')} days"
            end_date = sub.get("end_date", "Never")
            if end_date != "Never":
                try:
                    end_dt = datetime.datetime.fromisoformat(end_date)
                    end_date = f"<t:{int(end_dt.timestamp())}:R>"
                except:
                    pass
            
            embed.add_field(
                f"User {user_id}",
                f"Duration: {duration}\nEnds: {end_date}",
                inline=True
            )
    
    await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot):
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)
