
import hikari
import lightbulb
from receiptgen import role_manager

plugin = lightbulb.Plugin("test-role")

@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option(name="member", description="User to test role on", required=True, type=hikari.Member)
@lightbulb.command(name="test_role", description="Test role assignment functionality")
@lightbulb.implements(lightbulb.SlashCommand)
async def test_role(ctx: lightbulb.Context):
    member = getattr(ctx.options, "member")
    
    response = await ctx.respond("Testing role functionality...", flags=hikari.MessageFlag.EPHEMERAL)
    
    rm = role_manager.get_role_manager()
    if not rm:
        await response.edit("❌ Role manager not initialized")
        return
    
    # Test 1: Verify current role status
    verification = await rm.verify_role_assignment(ctx.guild_id, member.id)
    
    # Test 2: Try to assign role
    assignment = await rm.assign_access_role(ctx.guild_id, member.id)
    
    # Test 3: Verify role was assigned
    verification_after = await rm.verify_role_assignment(ctx.guild_id, member.id)
    
    result = f"""**Role Test Results for {member.mention}:**

**Before Assignment:**
✅ {verification['message']}

**Assignment Attempt:**
{'✅' if assignment['success'] else '❌'} {assignment['message']}

**After Assignment:**
✅ {verification_after['message']}

**Summary:** {'Success' if assignment['success'] and verification_after['has_role'] else 'Failed'}
"""
    
    await response.edit(result)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
