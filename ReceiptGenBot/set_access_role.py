
#!/usr/bin/env python3
import asyncio
from receiptgen import database

async def set_access_role():
    guild_id = 1395873913514229881  # Your guild ID
    role_id = 1397929996340953170   # The access role ID you want to set
    
    print(f"Setting access role {role_id} for guild {guild_id}...")
    
    guild_db = database.GuildAPI(guild_id=guild_id)
    result = await guild_db.updater_guild(access_role=role_id)
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print("✅ Access role set successfully!")
        
        # Verify the change
        guild_data = await guild_db.get_guild()
        print(f"Current access role: {guild_data.get('access_role')}")

if __name__ == "__main__":
    asyncio.run(set_access_role())
