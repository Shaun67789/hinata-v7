import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from telegram import ChatPermissions

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.responses import FileResponse
import bot  # Import the bot module
import database
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(f"----- SYSTEM INFO -----")
    print(f"Python Version: {sys.version}")
    print(f"-----------------------")
    # Start the bot as a background task
    asyncio.create_task(bot.start_bot())
    # Start auto-cleanup task
    asyncio.create_task(auto_cleanup_task())
    bot.logger.info("Web Dashboard Started")
    yield
    # Shutdown logic
    await bot.stop_bot()

app = FastAPI(title="Hinata Bot Dashboard", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ControlAction(BaseModel):
    action: str

class BroadcastMsg(BaseModel):
    target: str
    message: str

class CommandExec(BaseModel):
    command: str
    chat_id: str = None
    user_id: str = None

class TokenUpdate(BaseModel):
    token: str

@app.get("/api/config")
async def get_config():
    """Returns current bot configuration (excluding full token for security)."""
    # Just return masked token for UI
    try:
        with open(bot.BOT_TOKEN_FILE, "r") as f:
            t = f.read().strip()
            masked = t[:5] + "..." + t[-5:] if len(t) > 10 else "Invalid Token"
    except:
        masked = "Not Found"
        
    return {
        "token": masked,
        "welcome_img": bot.CONFIG.get("welcome_img"),
        "fallback_img": bot.CONFIG.get("fallback_img"),
        "global_access": bot.CONFIG.get("global_access")
    }

@app.post("/api/token")
async def update_token(data: TokenUpdate):
    """Updates the bot token in token.txt."""
    try:
        with open(bot.BOT_TOKEN_FILE, "w") as f:
            f.write(data.token.strip())
        return {"success": True, "message": "Token updated successfully. Restart the bot to apply."}
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class ConfigUpdate(BaseModel):
    welcome_img: str = None
    fallback_img: str = None

@app.post("/api/config-update")
async def update_config(data: ConfigUpdate):
    """Updates bot configuration (images, etc.)."""
    try:
        if data.welcome_img:
            bot.CONFIG["welcome_img"] = data.welcome_img
        if data.fallback_img:
            bot.CONFIG["fallback_img"] = data.fallback_img
        bot.save_config(bot.CONFIG)
        return {"success": True, "message": "Neural configuration updated."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download_db")
async def download_db():
    """Allows the owner to download the bot's SQLite database file."""
    db_path = "bot.db"
    if os.path.exists(db_path):
        return FileResponse(path=db_path, filename="bot.db", media_type="application/octet-stream")
    return JSONResponse(status_code=404, content={"error": "Database file not found."})

@app.get("/api/data")
async def get_data():
    """Returns all users and groups with full metadata."""
    users = database.get_all_users()
    groups = database.get_all_groups()
    broadcasts = database.get_all_broadcasts()
    
    return {
        "stats": {
            "total_users": len(users),
            "total_groups": len(groups),
            "broadcasts": len(broadcasts),
            "uptime": bot.get_uptime(),
            "status": bot.STATS.get("status", "online"),
            "global_access": bot.CONFIG.get("global_access", True)
        },
        "users": users,
        "groups": groups,
        "broadcasts": broadcasts,
        "banned_users": bot.CONFIG.get("banned_users", [])
    }


@app.get("/api/logs")
async def get_logs():
    # Read last 50 lines from log file
    if os.path.exists(bot.LOG_FILE):
        with open(bot.LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-50:]
    return ["Log file not found."]

@app.post("/api/control")
async def control_bot(data: ControlAction):
    if data.action == "restart":
        await bot.stop_bot()
        asyncio.create_task(bot.start_bot())
        return {"success": True}
    elif data.action == "clear_logs":
        if os.path.exists(bot.LOG_FILE):
            open(bot.LOG_FILE, "w").close()
        return {"success": True}
    elif data.action == "toggle_access":
        bot.CONFIG["global_access"] = not bot.CONFIG.get("global_access", True)
        bot.save_config(bot.CONFIG)
        return {"success": True, "new_status": bot.CONFIG["global_access"]}
    elif data.action == "delete_broadcast":
        history = bot.read_json("broadcast_history.json", [])
        if not history:
            return {"success": False, "error": "No broadcast history found"}
        
        s = f = 0
        if not bot.app:
            return {"success": False, "error": "Bot not initialized"}
            
        for entry in history:
            try:
                await bot.app.bot.delete_message(chat_id=entry['chat_id'], message_id=entry['message_id'])
                s += 1
            except:
                f += 1
        
        bot.write_json("broadcast_history.json", [])
        return {"success": True, "deleted": s, "failed": f}
    elif data.action == "toggle_bot":
        if bot.STATS.get("status") == "online":
            await bot.stop_bot()
        else:
            asyncio.create_task(bot.start_bot())
        return {"success": True}
    elif data.action == "track_users":
        # Launch tracking as background task
        asyncio.create_task(track_all_users())
        return {"success": True, "message": "User tracking initiated in background"}
    elif data.action == "clear_downloads":
        count = 0
        for f in os.listdir("downloads"):
            try:
                os.remove(os.path.join("downloads", f))
                count += 1
            except: pass
        return {"success": True, "message": f"Cleared {count} files from neural core."}
    return {"success": False, "error": "Unknown action"}

@app.get("/api/files")
async def list_files():
    files = []
    folder = "downloads"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isfile(path):
                stats = os.stat(path)
                files.append({
                    "name": f,
                    "size": f"{stats.st_size / (1024*1024):.2f} MB",
                    "time": bot.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    return files

async def auto_cleanup_task():
    """Background task to clear downloads every 10 minutes."""
    while True:
        await asyncio.sleep(600) # 10 minutes
        try:
            now = bot.time.time()
            count = 0
            for f in os.listdir("downloads"):
                path = os.path.join("downloads", f)
                if os.path.isfile(path):
                    # Remove files older than 10 mins
                    if now - os.stat(path).st_mtime > 600:
                        os.remove(path)
                        count += 1
            if count > 0:
                bot.logger.info(f"Auto-cleanup: {count} expired files removed from registry.")
        except Exception as e:
            bot.logger.error(f"Cleanup Error: {e}")

async def track_all_users():
    """Background task to track all users metadata."""
    if not bot.app: return
    users = database.get_all_users()
    bot.logger.info(f"Starting tracking for {len(users)} users...")
    for u in users:
        try:
            chat = await bot.app.bot.get_chat(u['id'])
            database.add_user(u['id'], chat.full_name, chat.username)
            # Sleep a bit to avoid flood limits
            await asyncio.sleep(0.5)
        except Exception as e:
            bot.logger.error(f"Failed to track user {u['id']}: {e}")
    bot.logger.info("User tracking complete.")

@app.get("/api/broadcasts")
async def get_broadcast_history():
    return database.get_all_broadcasts()

@app.delete("/api/broadcasts/{b_id}")
async def delete_broadcast_item(b_id: int):
    try:
        b = database.get_broadcast(b_id)
        if not b:
            return {"success": False, "error": "Broadcast not found"}
        
        # Delete messages from Telegram
        msg_ids = json.loads(b['message_ids'])
        s = f = 0
        if bot.app:
            for chat_id, message_id in msg_ids.items():
                try:
                    await bot.app.bot.delete_message(chat_id=int(chat_id), message_id=int(message_id))
                    s += 1
                except:
                    f += 1
        
        # Delete from DB
        database.delete_broadcast_record(b_id)
        return {"success": True, "deleted": s, "failed": f}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/broadcast")
async def api_broadcast(data: BroadcastMsg):
    try:
        if not bot.app:
            return {"success": False, "error": "Bot not initialized"}
        
        msg_ids_map = {}
        s_users = f_users = s_groups = f_groups = 0
        
        if data.target == "all" or data.target == "users":
            users = database.get_all_users()
            for u in users:
                uid = u['id']
                try: 
                    sent = await bot.app.bot.send_message(chat_id=uid, text=data.message)
                    msg_ids_map[str(sent.chat_id)] = sent.message_id
                    s_users += 1
                except:
                    f_users += 1
        
        if data.target == "all" or data.target == "groups":
            groups = database.get_all_groups()
            for g in groups:
                gid = g['id']
                try: 
                    sent = await bot.app.bot.send_message(chat_id=gid, text=data.message)
                    msg_ids_map[str(sent.chat_id)] = sent.message_id
                    s_groups += 1
                except:
                    f_groups += 1
    
        # Save to DB
        database.add_broadcast(data.message, data.target, s_users + s_groups, f_users + f_groups, msg_ids_map)
        
        # Update Stats
        bot.update_stats(s_users, f_users, s_groups, f_groups)
        bot.STATS["broadcasts"] = bot.STATS.get("broadcasts", 0) + 1

        return {
            "status": "success", 
            "sent": s_users + s_groups, 
            "failed": f_users + f_groups,
            "detail": f"Sent to {s_users} users & {s_groups} groups"
        }
    except Exception as e:
        bot.logger.error(f"API Broadcast Error: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/api/execute")
async def execute_command(data: CommandExec):
    """Execute owner commands from dashboard."""
    try:
        if not bot.app:
            return {"success": False, "error": "Bot not initialized"}
        
        chat_id = int(data.chat_id) if data.chat_id else None
        user_id = int(data.user_id) if data.user_id else None
        
        if data.command == "ban":
            if not chat_id or not user_id:
                return {"success": False, "error": "Chat ID and User ID required"}
            await bot.app.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            return {"success": True, "message": f"User {user_id} banned from {chat_id}"}
        
        elif data.command == "unban":
            if not chat_id or not user_id:
                return {"success": False, "error": "Chat ID and User ID required"}
            await bot.app.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            return {"success": True, "message": f"User {user_id} unbanned from {chat_id}"}
        
        elif data.command == "kick":
            if not chat_id or not user_id:
                return {"success": False, "error": "Chat ID and User ID required"}
            await bot.app.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await bot.app.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            return {"success": True, "message": f"User {user_id} kicked from {chat_id}"}
        
        elif data.command == "mute":
            if not chat_id or not user_id:
                return {"success": False, "error": "Chat ID and User ID required"}
            await bot.app.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            return {"success": True, "message": f"User {user_id} muted in {chat_id}"}
        
        elif data.command == "unmute":
            if not chat_id or not user_id:
                return {"success": False, "error": "Chat ID and User ID required"}
            await bot.app.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True
                )
            )
            return {"success": True, "message": f"User {user_id} unmuted in {chat_id}"}
        
        elif data.command == "addadmin":
            if not chat_id or not user_id:
                return {"success": False, "error": "Chat ID and User ID required"}
            await bot.app.bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
            return {"success": True, "message": f"User {user_id} promoted to admin in {chat_id}"}
        
        return {"success": False, "error": "Unknown command"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Use environment variables for port (Render uses PORT env)
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
