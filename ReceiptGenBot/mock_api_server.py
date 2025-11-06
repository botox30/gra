from aiohttp import web
import json
import asyncio

# Mock data storage
guilds = {}
guild_members = {}
discord_users = {}
tickets = {}

routes = web.RouteTableDef()

# Guild endpoints
@routes.get('/api/guild/{guild_id}/')
async def get_guild(request):
    guild_id = request.match_info['guild_id']
    if guild_id not in guilds:
        # Create a default guild with active subscription
        guilds[guild_id] = {
            "guild_id": int(guild_id),
            "owner_id": None,
            "name": "Test Guild",
            "access_role": None,
            "notification_channel": None,
            "purchase_channel": None,
            "has_subscription": True,  # This indicates the service is active
            "subscription_active": True,
            "subscription_end": "2025-12-31T23:59:59",  # Future date
            "disabled": False  # This prevents the service disabled message
        }
    return web.json_response(guilds[guild_id])

@routes.post('/api/guild/')
async def create_guild(request):
    data = await request.json()
    guild_id = str(data['guild_id'])
    guilds[guild_id] = {
        "guild_id": int(guild_id),
        "owner_id": data.get('owner_id'),
        "name": data.get('name'),
        "access_role": None,
        "notification_channel": None,
        "purchase_channel": None
    }
    return web.json_response({"success": True})

@routes.patch('/api/guild/{guild_id}/')
async def update_guild(request):
    guild_id = request.match_info['guild_id']
    data = await request.json()

    if guild_id not in guilds:
        guilds[guild_id] = {
            "guild_id": int(guild_id),
            "access_role": None,
            "notification_channel": None,
            "purchase_channel": None
        }

    guilds[guild_id].update(data)
    return web.json_response({"success": True})

# Guild member endpoints
@routes.get('/api/guild/{guild_id}/member/{member_id}/')
async def get_guild_member(request):
    guild_id = request.match_info['guild_id']
    member_id = request.match_info['member_id']
    key = f"{guild_id}_{member_id}"

    if key not in guild_members:
        # Create a default guild member with access
        guild_members[key] = {
            "guild": int(guild_id),
            "member": int(member_id),
            "email": "fakeobywatell@gmail.com",
            "has_access": True,  # Grant access by default for testing
            "access_end": "2025-12-31T23:59:59"
        }

    return web.json_response(guild_members[key])

@routes.post('/api/guild-member/')
async def create_guild_member(request):
    data = await request.json()
    key = f"{data['guild']}_{data['member']}"
    guild_members[key] = {
        "guild": data['guild'],
        "member": data['member'],
        "has_access": data.get('days', 0) > 0,
        "access_end": None,
        "email": data.get('email')
    }
    return web.json_response({"success": True})

@routes.patch('/api/guild/{guild_id}/member/{member_id}/')
async def update_guild_member(request):
    guild_id = request.match_info['guild_id']
    member_id = request.match_info['member_id']
    key = f"{guild_id}_{member_id}"
    data = await request.json()

    if key not in guild_members:
        guild_members[key] = {
            "guild": guild_id,
            "member": member_id,
            "has_access": False,
            "access_end": None,
            "email": None
        }

    guild_members[key].update(data)
    return web.json_response({"success": True})

# Subscription status endpoint
@routes.get('/api/guild/{guild_id}/subscription/')
async def get_guild_subscription(request):
    guild_id = request.match_info['guild_id']
    return web.json_response({
        "success": True,
        "active": True,
        "subscription_end": "2025-12-31T23:59:59"
    })

# Discord user endpoints
@routes.get('/api/discord-user/{user_id}/')
async def get_discord_user(request):
    user_id = request.match_info['user_id']
    if user_id in discord_users:
        return web.json_response({"success": True, "user": discord_users[user_id]})
    return web.json_response({"success": False})

@routes.post('/api/discord-user/')
async def create_discord_user(request):
    data = await request.json()
    user_id = data['discord_user_id']
    discord_users[user_id] = {
        "discord_user_id": user_id,
        "email": data.get('email'),
        "has_access": False,
        "access_end": None
    }
    return web.json_response({"success": True})

@routes.patch('/api/discord-user/{user_id}/update/')
async def update_discord_user(request):
    user_id = request.match_info['user_id']
    data = await request.json()

    if user_id not in discord_users:
        discord_users[user_id] = {
            "discord_user_id": user_id,
            "email": None,
            "has_access": False,
            "access_end": None
        }

    discord_users[user_id].update(data)
    return web.json_response({"success": True})

# Other endpoints
@routes.get('/api/users-without-access/')
async def users_without_access(request):
    return web.json_response([])

@routes.get('/api/expired-access-users/')
async def expired_access_users(request):
    return web.json_response({"success": True, "users": []})

@routes.post('/api/ticket/create/')
async def create_ticket(request):
    data = await request.json()
    ticket_id = f"ticket_{len(tickets)}"
    tickets[data['channel_id']] = {
        "ticket_id": ticket_id,
        "channel_id": data['channel_id'],
        "user_id": data['user_id']
    }
    return web.json_response({"success": True, "ticket": {"ticket_id": ticket_id}})

@routes.post('/api/ticket/delete/')
async def delete_ticket(request):
    data = await request.json()
    if data['channel_id'] in tickets:
        del tickets[data['channel_id']]
    return web.json_response({"success": True})

@routes.get('/api/ticket/not-deleted/')
async def get_tickets(request):
    return web.json_response({"channels": list(tickets.keys())})

# Catch-all for other endpoints
@routes.post('/api/{path:.*}')
async def catch_all_post(request):
    return web.json_response({"success": True})

@routes.get('/api/{path:.*}')
async def catch_all_get(request):
    return web.json_response({"success": True, "data": []})

async def start_mock_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("Mock API server started on port 8000")

    # Keep the server running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour at a time
    except KeyboardInterrupt:
        print("Shutting down mock API server...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(start_mock_server())