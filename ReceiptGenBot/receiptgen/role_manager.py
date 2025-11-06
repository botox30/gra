
import hikari
import asyncio
from receiptgen import database

class RoleManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def assign_access_role(self, guild_id: int, user_id: int, force_assign: bool = False):
        """
        Assign access role to a user with comprehensive error handling
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            force_assign: If True, assigns role even if database operation fails
        
        Returns:
            dict with success status and message
        """
        try:
            # Get guild data for role ID
            guild_db = database.GuildAPI(guild_id=guild_id)
            guild_data = await guild_db.get_guild()
            access_role = guild_data.get("access_role")
            
            if not access_role:
                return {
                    "success": False,
                    "message": "No access role configured in guild settings"
                }
            
            role_id = int(access_role)
            
            # Check if user exists in guild
            try:
                member = await self.bot.rest.fetch_member(guild=guild_id, user=user_id)
            except hikari.NotFoundError:
                return {
                    "success": False,
                    "message": "User not found in guild"
                }
            
            # Check if role exists
            try:
                role = await self.bot.rest.fetch_role(guild=guild_id, role=role_id)
            except hikari.NotFoundError:
                return {
                    "success": False,
                    "message": f"Role {role_id} not found in guild"
                }
            
            # Check if user already has the role
            member_roles = [role.id for role in member.get_roles()]
            if role_id in member_roles:
                return {
                    "success": True,
                    "message": f"User already has role {role.name}"
                }
            
            # Assign the role
            try:
                await self.bot.rest.add_role_to_member(
                    guild=guild_id,
                    user=user_id,
                    role=role_id
                )
                
                return {
                    "success": True,
                    "message": f"Successfully assigned role {role.name} ({role_id})"
                }
                
            except hikari.ForbiddenError:
                return {
                    "success": False,
                    "message": "Bot lacks permission to assign this role"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to assign role: {str(e)}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Role assignment error: {str(e)}"
            }
    
    async def remove_access_role(self, guild_id: int, user_id: int):
        """
        Remove access role from a user
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
        
        Returns:
            dict with success status and message
        """
        try:
            # Get guild data for role ID
            guild_db = database.GuildAPI(guild_id=guild_id)
            guild_data = await guild_db.get_guild()
            access_role = guild_data.get("access_role")
            
            if not access_role:
                return {
                    "success": False,
                    "message": "No access role configured in guild settings"
                }
            
            role_id = int(access_role)
            
            # Remove the role
            try:
                await self.bot.rest.remove_role_from_member(
                    guild=guild_id,
                    user=user_id,
                    role=role_id
                )
                
                return {
                    "success": True,
                    "message": f"Successfully removed role {role_id}"
                }
                
            except hikari.ForbiddenError:
                return {
                    "success": False,
                    "message": "Bot lacks permission to remove this role"
                }
            except hikari.NotFoundError:
                return {
                    "success": True,
                    "message": "User didn't have the role or role doesn't exist"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to remove role: {str(e)}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Role removal error: {str(e)}"
            }
    
    async def verify_role_assignment(self, guild_id: int, user_id: int):
        """
        Verify if user has the access role
        
        Args:
            guild_id: Discord guild ID  
            user_id: Discord user ID
        
        Returns:
            dict with verification status
        """
        try:
            # Get guild data for role ID
            guild_db = database.GuildAPI(guild_id=guild_id)
            guild_data = await guild_db.get_guild()
            access_role = guild_data.get("access_role")
            
            if not access_role:
                return {
                    "has_role": False,
                    "message": "No access role configured"
                }
            
            role_id = int(access_role)
            
            # Get member and check roles
            try:
                member = await self.bot.rest.fetch_member(guild=guild_id, user=user_id)
                member_roles = [role.id for role in member.get_roles()]
                
                has_role = role_id in member_roles
                
                return {
                    "has_role": has_role,
                    "role_id": role_id,
                    "message": f"User {'has' if has_role else 'does not have'} access role"
                }
                
            except hikari.NotFoundError:
                return {
                    "has_role": False,
                    "message": "User not found in guild"
                }
            
        except Exception as e:
            return {
                "has_role": False,
                "message": f"Verification error: {str(e)}"
            }

# Global role manager instance (will be initialized when bot starts)
role_manager = None

def init_role_manager(bot):
    """Initialize the global role manager"""
    global role_manager
    role_manager = RoleManager(bot)
    return role_manager

def get_role_manager():
    """Get the global role manager instance"""
    return role_manager
