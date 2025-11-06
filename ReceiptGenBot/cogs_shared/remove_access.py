
import datetime
import hikari
import lightbulb
from receiptgen import database, utils

plugin = lightbulb.Plugin("remove-access")

@plugin.command
@lightbulb.decorators.app_command_permissions(hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option(name="member", description="User to remove access from", required=True, type=hikari.Member)
@lightbulb.command(name="remove_access", description="Remove User Access")
@lightbulb.implements(lightbulb.SlashCommand)
async def remove_access(ctx: lightbulb.Context):
    member = getattr(ctx.options, "member")

    response = await ctx.respond("Removing access from member...", flags=hikari.MessageFlag.EPHEMERAL)

    try:
        # Step 1: Remove database access completely
        db = database.GuildMemberAPI(guild_id=ctx.guild_id, member_id=member.id)
        
        # Check if member exists first
        try:
            existing_member = await db.get_guild_member()
            if existing_member.get("error"):
                await response.edit("User doesn't have any access to remove")
                return
        except Exception:
            await response.edit("User doesn't have any access to remove")
            return

        print(f"DEBUG: Removing database access for user {member.id}")
        # Remove access by setting remove_access=True
        result = await db.update_guild_member(remove_access=True)
        
        if result and result.get("error"):
            await response.edit(f"Database error: {result['error']}")
            return

        print(f"DEBUG: Database removal result: {result}")

        # Step 2: Remove role if configured and user has it
        guild_db = database.GuildAPI(guild_id=ctx.guild_id)
        guild_data = await guild_db.get_guild()
        access_role = guild_data.get("access_role")
        
        role_message = ""
        
        if access_role:
            try:
                role_id = int(access_role)
                print(f"DEBUG: Checking role {role_id} for removal")
                
                # Check if user actually has the role
                try:
                    member_obj = await ctx.bot.rest.fetch_member(guild=ctx.guild_id, user=member.id)
                    current_roles = [role.id for role in member_obj.get_roles()]
                    
                    if role_id in current_roles:
                        # Remove the role
                        await ctx.bot.rest.remove_role_from_member(
                            guild=ctx.guild_id,
                            user=member.id,
                            role=role_id
                        )
                        role_message = " and removed access role"
                        print(f"DEBUG: Successfully removed role {role_id}")
                    else:
                        role_message = " (user didn't have access role)"
                        print(f"DEBUG: User didn't have role {role_id}")
                        
                except hikari.ForbiddenError:
                    role_message = " (bot lacks permission to remove role)"
                    print("DEBUG: Bot lacks permission to remove role")
                except hikari.NotFoundError:
                    role_message = " (member or role not found)"
                    print("DEBUG: Member or role not found")
                except Exception as role_error:
                    role_message = f" (role removal failed: {str(role_error)})"
                    print(f"DEBUG: Role removal error: {role_error}")
                    
            except ValueError:
                role_message = " (invalid role ID format)"
                print(f"DEBUG: Invalid role ID: {access_role}")
            except Exception as e:
                role_message = f" (role processing error: {str(e)})"
                print(f"DEBUG: Role processing error: {e}")

        # Send success message
        success_message = f"Successfully removed ALL access from member{role_message}"
        await response.edit(success_message)

    except Exception as e:
        print(f"ERROR in remove_access: {e}")
        import traceback
        traceback.print_exc()
        await response.edit(f"Command failed: {str(e)}")

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
