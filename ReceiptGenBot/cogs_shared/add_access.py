import datetime
import hikari
import lightbulb
from receiptgen import database, utils
from receiptgen.role_manager import RoleManager
from receiptgen.subscription_manager import ManualSubscriptionManager

plugin = lightbulb.Plugin("add-access")

@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option(name="member", description="User to add access to", required=True, type=hikari.Member)
@lightbulb.option(name="days", description="Amount of days", required=False, type=int)
@lightbulb.option(name="forever", description="Forever access", required=False, type=bool)
@lightbulb.command(name="add_access", description="Add User Access")
@lightbulb.implements(lightbulb.SlashCommand)
async def add_access(ctx: lightbulb.Context):
    days = getattr(ctx.options, "days", None)
    forever = getattr(ctx.options, "forever", None)
    member = getattr(ctx.options, "member")

    response = await ctx.respond("Adding access to member...", flags=hikari.MessageFlag.EPHEMERAL)

    # Validate input
    if not days and not forever:
        await response.edit("Please specify either days OR forever access")
        return

    if days and forever:
        await response.edit("Pick one Option (either days OR forever, not both)")
        return

    try:
        # Database operation
        db = database.GuildMemberAPI(guild_id=ctx.guild_id, member_id=member.id)

        # Check if member exists first
        existing_member = None
        try:
            existing_member = await db.get_guild_member()
            print(f"DEBUG: Existing member: {existing_member}")
        except Exception as e:
            print(f"DEBUG: No existing member: {e}")

        # Create or update based on what we're adding
        if days:
            print(f"DEBUG: Adding {days} days access")
            if existing_member and not existing_member.get("error"):
                # Update existing with specific days
                result = await db.update_guild_member(days=days)
            else:
                # Create new with specific days
                result = await db.create_guild_member(
                    guild_id=ctx.guild_id,
                    member_id=member.id,
                    days=days
                )
            duration_text = f"{days} days"
        else:
            print("DEBUG: Adding forever access")
            if existing_member and not existing_member.get("error"):
                # Update existing for forever (no days parameter means forever)
                result = await db.update_guild_member()
            else:
                # Create new for forever (no days parameter means forever)
                result = await db.create_guild_member(
                    guild_id=ctx.guild_id,
                    member_id=member.id
                )
            duration_text = "forever"

        print(f"DEBUG: Database update result: {result}")
        
        # Let's also check what the database now contains
        try:
            check_member = await db.get_guild_member()
            print(f"DEBUG: Member data after update: {check_member}")
        except Exception as check_error:
            print(f"DEBUG: Could not check member data: {check_error}")

        # Backup: Save to manual subscription file
        try:
            manual_sub = ManualSubscriptionManager()
            manual_result = manual_sub.add_subscription(
                user_id=member.id,
                days=days,
                guild_id=ctx.guild_id
            )
            print(f"DEBUG: Manual subscription backup saved: {manual_result}")
        except Exception as backup_error:
            print(f"DEBUG: Manual subscription backup failed: {backup_error}")

        # Assign role if configured
        guild_db = database.GuildAPI(guild_id=ctx.guild_id)
        guild_data = await guild_db.get_guild()
        access_role = guild_data.get("access_role")

        role_message = " (no access role configured in guild settings)"

        if access_role:
            try:
                role_id = int(access_role)
                print(f"DEBUG: Attempting to assign role {role_id}")

                # Check if user already has role
                try:
                    member_obj = await ctx.bot.rest.fetch_member(guild=ctx.guild_id, user=member.id)
                    current_roles = [role.id for role in member_obj.get_roles()]

                    if role_id in current_roles:
                        role_message = f" (user already has role)"
                        print(f"DEBUG: User already has role {role_id}")
                    else:
                        # Try to assign role
                        print(f"DEBUG: Attempting to assign role {role_id} in guild {ctx.guild_id} to user {member.id}")
                        await ctx.bot.rest.add_role_to_member(
                            guild=ctx.guild_id,
                            user=member.id,
                            role=role_id
                        )
                        role_message = f" and assigned access role"
                        print(f"DEBUG: Successfully assigned role {role_id}")

                except hikari.ForbiddenError:
                    role_message = f" (bot lacks permission to assign role)"
                    print("DEBUG: Bot lacks permission")
                except hikari.NotFoundError:
                    role_message = f" (role {role_id} not found)"
                    print("DEBUG: Role not found")
                except Exception as role_error:
                    role_message = f" (role assignment failed: {str(role_error)})"
                    print(f"DEBUG: Role assignment error: {role_error}")

            except ValueError:
                role_message = f" (invalid role ID format)"
                print(f"DEBUG: Invalid role ID: {access_role}")
            except Exception as e:
                role_message = f" (role error: {str(e)})"
                print(f"DEBUG: Role error: {e}")

        # Send success message
        success_message = f"Successfully added {duration_text} access to member{role_message}"
        await response.edit(success_message)

    except Exception as e:
        print(f"ERROR in add_access: {e}")
        import traceback
        traceback.print_exc()
        await response.edit(f"Command failed: {str(e)}")

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)