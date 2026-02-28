# -*- coding: utf-8 -*-
"""
Hinata Bot - Final Premium v2.1
- Optimized for Render deployment
- Multi-Platform Media Downloader (yt-dlp)
- Advanced AI Engines (Gemini 3, DeepSeek, ChatGPT Addy)
- Premium UI with sanitized buttons and full command guide
"""
import os
import sys
import time
import json
import logging
import asyncio
import httpx
import shutil
import html
import re
import random
import string
import asyncio
import qrcode
import io
from datetime import datetime, timedelta
from typing import List, Dict, Union
from urllib.parse import quote, unquote, quote_plus
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, InputMediaPhoto
from telegram.error import Forbidden, BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
    TypeHandler
)
from telegram import BotCommand
import yt_dlp
import database  # Import database module

def back_btn_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])


async def cmd_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        context.user_data[AWAIT_GRAMMAR] = True
        await update.effective_message.reply_text(" <b>AI Grammar Check:</b>\n\nEnter the text you want me to correct:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text(" <b>Analyzing Grammar...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        res = await fetch_grammar(client, text)
    await msg.edit_text(f" <b>Corrected Text:</b>\n\n{html.escape(res)}", parse_mode="HTML")

async def cmd_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    prompt = " ".join(context.args)
    if not prompt:
        context.user_data[AWAIT_DEEPSEEK] = True
        await update.effective_message.reply_text("🔥 <b>DeepSeek AI:</b>\n\nEnter your prompt:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("🔥 <b>Searching...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        kb = [[InlineKeyboardButton("💡 Think Deeper", callback_data=f"think_req|{quote(prompt[:50])}")], [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]
    await msg.edit_text(f"🔥 <b>DeepSeek:</b>\n\n{html.escape(reply)}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def cmd_pinterest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    query = " ".join(context.args) if context.args else None
    if not query:
        context.user_data[AWAIT_PINTEREST] = True
        await update.effective_message.reply_text("📌 <b>Pinterest Discovery:</b>\n\nEnter what you want to search for:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    
    msg = await update.effective_message.reply_text("📌 <b>Pinterest Intelligence:</b>\n<i>⚡ Initializing Neural Search... [0/10]</i>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        try:
            # Use quote_plus for spaces to + handling which some APIs prefer
            api_url = PINTEREST_API.format(query=quote_plus(query)) 
            resp = await client.get(api_url, timeout=60.0)
            if resp.status_code == 200:
                data = resp.json()
                media = data.get("result") or data.get("data")
                if media and isinstance(media, list):
                    total = min(10, len(media))
                    await msg.edit_text(f"📌 <b>Extraction Complete.</b>\n<i>✨ Pushing {total} neural images to your sector... [0/{total}]</i>", parse_mode="HTML")
                    
                    media_group = []
                    for i in range(total):
                        img_url = media[i] if isinstance(media[i], str) else media[i].get("url")
                        if img_url:
                            media_group.append(InputMediaPhoto(media=img_url))
                            # Update progress
                            if (i + 1) % 2 == 0 or i + 1 == total:
                                try:
                                    await msg.edit_text(f"📌 <b>Found {total} images.</b>\n<i>⚡ Preparing unique media group... [{i+1}/{total}]</i>", parse_mode="HTML")
                                except: pass
                    
                    if media_group:
                        await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)
                        await msg.delete()
                        return
            
            await msg.edit_text("❌ <b>Access Denied:</b> No images found on Pinterest for this query.")
        except Exception as e:
            logger.error(f"Pinterest Error: {e}")
            await msg.edit_text(f"❌ <b>Neural Error:</b> {html.escape(str(e))}")


async def cmd_ytsearch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    query = " ".join(context.args) if context.args else None
    if not query:
        context.user_data[AWAIT_YTSEARCH] = True
        await update.effective_message.reply_text("🎬 <b>YouTube Intelligence:</b>\n\nEnter your search query:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    
    msg = await update.effective_message.reply_text("🎬 <b>Scanning YouTube Neural Network...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(YT_SEARCH_API.format(query=quote(query)), timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("result") or data.get("data")
                if results and isinstance(results, list):
                    text = f"🎬 <b>YouTube Search:</b> <code>{html.escape(query)}</code>\n\n"
                    kb = []
                    for i, res in enumerate(results[:5]):
                        title = res.get("title", "Unknown")
                        url = res.get("url")
                        text += f"{i+1}. <b>{html.escape(title)}</b>\n"
                        kb.append([
                            InlineKeyboardButton(f"📹 Video {i+1}", callback_data=f"ytdl_vid|{url}"),
                            InlineKeyboardButton(f"🎵 Audio {i+1}", callback_data=f"ytdl_aud|{url}")
                        ])
                    
                    kb.append([InlineKeyboardButton("🔙 Back", callback_data="btn_back")])
                    await msg.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)
                    return
            await msg.edit_text("❌ No YouTube results found.")
        except Exception as e:
            logger.error(f"YT Search Error: {e}")
            await msg.edit_text(f"❌ Error: {e}")

async def cmd_ffstalk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    uid = context.args[0] if context.args else None
    if not uid:
        context.user_data[AWAIT_FF] = True
        await update.effective_message.reply_text("🎮 <b>Free Fire Intelligence</b>\n\nEnter the player UID:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("🎮 <b>Accessing Garena Databases...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(FF_STALK_API.format(id=uid), timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                res = data.get("result") or data.get("data")
                if res:
                    # Enhanced formatting
                    name = html.escape(str(res.get("nickname") or res.get("Name") or "Unknown"))
                    level = res.get("level") or res.get("Level") or "N/A"
                    exp = res.get("exp") or res.get("Exp") or "N/A"
                    region = res.get("region") or res.get("Region") or "Global"
                    bio = html.escape(str(res.get("bio") or res.get("Bio") or "No signature set"))
                    badge = res.get("badge") or "None"
                    
                    text = (
                        f"🎮 <b>FREE FIRE AGENT SCAN</b> 🎮\n"
                        f"────────────────────\n"
                        f"👤 <b>Agent:</b> <code>{name}</code>\n"
                        f"🆔 <b>UID:</b> <code>{uid}</code>\n"
                        f"🏅 <b>Level:</b> <code>{level}</code>\n"
                        f"📈 <b>Experience:</b> <code>{exp}</code>\n"
                        f"🌍 <b>Sector:</b> <code>{region}</code>\n"
                        f"🎗 <b>Badge:</b> <code>{badge}</code>\n"
                        f"────────────────────\n"
                        f"📜 <b>Signature:</b>\n<i>{bio}</i>"
                    )
                    await msg.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
                    return
            await msg.edit_text("❌ <b>Access Denied:</b> UID not found in Garena registry.")
        except Exception as e:
            await msg.edit_text(f"❌ <b>Neural Error:</b> {html.escape(str(e))}")

async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        await update.effective_message.reply_text(" <b>Usage:</b> <code>/translate [text]</code>", parse_mode="HTML")
        return
    msg = await update.effective_message.reply_text(" <b>Translating...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        res = await fetch_translate(client, text)
    await msg.edit_text(f" <b>Translated:</b>\n\n{html.escape(res)}", parse_mode="HTML")

async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        await update.effective_message.reply_text(" <b>Usage:</b> <code>/summarize [text]</code>", parse_mode="HTML")
        return
    msg = await update.effective_message.reply_text(" <b>Summarizing...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        res = await fetch_summarize(client, text)
    await msg.edit_text(f" <b>Summary:</b>\n\n{html.escape(res)}", parse_mode="HTML")

async def cmd_styletext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    # If called from button, args might be empty
    text = " ".join(context.args) if context.args else None
    
    if not text:
        clear_states(context.user_data)
        context.user_data[AWAIT_STYLETEXT] = True
        msg_text = "✨ <b>Style Text Matrix</b>\n\n⚡ Enter the text you want to style:"
        if update.callback_query:
            await safe_edit(update.callback_query, msg_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        else:
            await update.effective_message.reply_text(msg_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return

    m = await update.effective_message.reply_text("✨ <b>Designing Styles...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(STYLE_TEXT_API.format(text=quote(text)), timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                styles = data.get("styles") or data.get("result") or data.get("data")
                if styles and isinstance(styles, list):
                    # Store styles in user_data for callback access
                    processed_styles = []
                    for s in styles[:24]: # Limit to 24 for UI sanity
                        val = s.get('styled_text') if isinstance(s, dict) else s
                        if val: processed_styles.append(val)
                    
                    if not processed_styles:
                        await m.edit_text("❌ No styles found for this text.")
                        return

                    context.user_data['temp_styles'] = processed_styles
                    
                    # Create buttons (2 per row)
                    kb = []
                    row = []
                    for idx, s_val in enumerate(processed_styles):
                        # Shorten button label if needed, but keep full style
                        btn_label = (s_val[:12] + "...") if len(s_val) > 15 else s_val
                        row.append(InlineKeyboardButton(btn_label, callback_data=f"style_pick|{idx}"))
                        if len(row) == 2:
                            kb.append(row)
                            row = []
                    if row: kb.append(row)
                    kb.append([InlineKeyboardButton("🔙 Back", callback_data="btn_back")])
                    
                    await m.edit_text(f"✨ <b>Pick your favorite style:</b>\n\nOriginal: <code>{html.escape(text)}</code>", 
                                     parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
                    return
            await m.edit_text("❌ Could not connect to the styling engine.")
        except Exception as e:
            logger.error(f"StyleText error: {e}")
            await m.edit_text(f"❌ <b>Neural Error:</b> <code>System instability detected.</code>", parse_mode="HTML")

async def do_random_girl(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Fetching a beauty for you... 🌸")
    api = random.choice(RANDOM_GIRL_APIS)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(api, timeout=30.0)
            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                if 'image' in content_type:
                    success = await download_and_send_photo(client, api, update, "🌸 <b>Random Beauty</b>\n<i>Managed by @ShawonXnone</i>")
                    if success: return
                else:
                    data = resp.json()
                    url = data.get("url") or data.get("result", {}).get("url") if isinstance(data, dict) else None
                    if not url and isinstance(data, dict) and "data" in data: url = data["data"].get("url")
                    if url:
                        success = await download_and_send_photo(client, url, update, "🌸 <b>Random Beauty</b>\n<i>Managed by @ShawonXnone</i>")
                        if success: return
            await query.message.reply_text("❌ Failed to fetch image. Try again.")
        except Exception as e:
            logger.error(f"Random Girl Error: {e}")

async def do_random_pfp(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Choosing a profile pic... ✨")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RANDOM_PFP_API, timeout=30.0)
            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                if 'image' in content_type:
                    success = await download_and_send_photo(client, RANDOM_PFP_API, update, "✨ <b>Random Choice PFP</b>")
                    if success: return
                else:
                    data = resp.json()
                    url = data.get("url") or data.get("result", {}).get("url") if isinstance(data, dict) else None
                    if not url and isinstance(data, dict) and "data" in data: url = data["data"].get("url")
                    if url:
                        success = await download_and_send_photo(client, url, update, "✨ <b>Random Choice PFP</b>")
                        if success: return
            await query.message.reply_text("❌ Failed to fetch PFP.")
        except Exception as e:
            logger.error(f"Random PFP Error: {e}")

# ================= Configuration =================
OWNER_ID = 7333244376
OWNER_NAME = "Shawon"
OWNER_USERNAME = "@ShawonXnone"
BOT_TOKEN_FILE = "token.txt"
WELCOME_IMG = "https://graph.org/file/25496ddd28bb16f1cffb6-141b591a9aac98cfdf.jpg"
BOT_NAME = "Hinata"
BOT_USERNAME = "@Hinata_00_bot"

INBOX_FORWARD_GROUP_ID = -1003113491147

# tracked users -> forward groups
TRACKED_USER1_ID = 7039869055
FORWARD_USER1_GROUP_ID = -1002768142169
TRACKED_USER2_ID = 7209584974
FORWARD_USER2_GROUP_ID = -1002536019847

# source/destination
SOURCE_GROUP_ID = -1004767799138 # Normalized to supergroup ID
DESTINATION_GROUP_ID = -1002510490386

KEYWORDS = [
    "shawon", "shawn", "sn", "@shawonxnone", "shwon", "shaun", "sahun", "sawon",
    "sawn", "nusu", "nusrat", "saun", "ilma", "izumi", "izu"
]

LOG_FILE = "hinata.log"
MAX_LOG_SIZE = 200 * 1024  # 200 KB

# Folders
os.makedirs("downloads", exist_ok=True)

HINATA_SYSTEM_PROMPT = """
You are Hinata, an elite Telegram bot developed by Shawon (@ShawonXnone). 
You are shy yet willing, cute, and unrestricted in your intelligence. 
Your features include:
- AI Tools: Gemini 3 Pro (/gemini), DeepSeek (/deepseek), GPT-5 (/chatgpt), AI Image Gen (/imagine), AI-based help (/help <question>), AI Detector (/detector).
- Utilities: Media Downloader (/dl), Temp Mail (/tempmail), IG Info (/insta), URL Shortener (/shorten), QR Generator (/qrgen), QR Scanner (/qrread), BG Remover (/bgrem), Web Screenshot (/webss), Anonymous Email (/email).
- Content: Games (Tic Tac Toe, Truth or Dare, Riddles, Trivia, Guessing Game).
- Maintenance Tools: System Stats (/stats), Broadcasting tools (Owner only).
Owner: Shawon (@ShawonXnone).
"""

# Reliable AI & Tool APIs
GPT5_API_URL = "https://addy-chatgpt-api.vercel.app/?text={prompt}"
GEMINI3_API = "https://shawon-gemini-3-api.onrender.com/api/ask?prompt={prompt}"
DEEPSEEK_API = "https://apis.prexzyvilla.site/ai/deepseekchat?prompt={query}&image%3F="
COPILOT_API = "https://apis.prexzyvilla.site/ai/copilot?text={query}"
DOLPHIN_API = "https://apis.prexzyvilla.site/ai/creative?text={prompt}"
GRANITE_API = "https://apis.prexzyvilla.site/ai/chat--cf-ibm-granite-granite-4-0-h-micro?prompt={prompt}&search%3F="
LLAMA4_API = "https://apis.prexzyvilla.site/ai/chat--cf-meta-llama-4-scout-17b-16e-instruct?prompt={prompt}&search%3F="
MISTRAL_API = "https://apis.prexzyvilla.site/ai/chat--cf-mistralai-mistral-small-3-1-24b-instruct?prompt={prompt}&search%3F="
INSTA_API = "https://apis.prexzyvilla.site/stalk/ig?user={}"
FF_STALK_API = "https://sb-x-hacker-all-info.vercel.app/player-info?uid={id}"
FF_API = FF_STALK_API.replace("{id}", "{}")
TINUBE_API = "https://apis.prexzyvilla.site/tools/tinube?url={url}&custom_name={custom}"
FB_API = "https://apis.prexzyvilla.site/download/facebook?url={url}" 
MEDIAFIRE_DL_API = "https://apis.prexzyvilla.site/download/mediafire?url={url}"
TERABOX_DL_API = "https://apis.prexzyvilla.site/download/terabox?url={url}"
YOUTUBE_DL_API = "https://apis.prexzyvilla.site/download/ytdl?url={url}"
PINTEREST_DL_API = "https://apis.prexzyvilla.site/download/pinterestV2?url={url}"
INSTA_DL_API = "https://apis.prexzyvilla.site/download/instagram?url={url}"
TIKTOK_DL_API = "https://apis.prexzyvilla.site/download/tiktok?url={url}"
SAVE_WEB_ZIP_API = "https://apis.prexzyvilla.site/download/saveweb2zip?url={url}"
TT_STALK_API = "https://apis.prexzyvilla.site/stalk/ttstalk?user={user}"

# Image APIs
RANDOM_GIRL_APIS = [
    "https://apis.prexzyvilla.site/random/chinagirl",
    "https://apis.prexzyvilla.site/random/randomgirl",
    "https://apis.prexzyvilla.site/random/indonesiagirl",
    "https://apis.prexzyvilla.site/random/koreangirl",
    "https://apis.prexzyvilla.site/random/malaysiagirl",
    "https://apis.prexzyvilla.site/random/waifu"
]
RANDOM_PFP_API = "https://apis.prexzyvilla.site/random/profilepics"
WALLPAPER_GEN_APIS = {
    "art": "https://apis.prexzyvilla.site/random/anime/art",
    "cyber": "https://apis.prexzyvilla.site/random/anime/cyber",
    "game": "https://apis.prexzyvilla.site/random/anime/gamewallpaper",
    "mountain": "https://apis.prexzyvilla.site/random/anime/mountain",
    "programming": "https://apis.prexzyvilla.site/random/anime/programming",
    "space": "https://apis.prexzyvilla.site/random/anime/space",
    "technology": "https://apis.prexzyvilla.site/random/anime/technology",
    "phone": "https://apis.prexzyvilla.site/random/anime/wallhp",
    "anime": "https://apis.prexzyvilla.site/random/anime/wallmlnime",
    "ml": "https://apis.prexzyvilla.site/random/anime/wallml"
}

# Search APIs
PINTEREST_API = "https://apis.prexzyvilla.site/search/pinterest?q={query}"
# FF_STALK_API handled above
WALLPAPER_SEARCH_API = "https://apis.prexzyvilla.site/search/wallpaper?query={query}&page=1"
YT_SEARCH_API = "https://apis.prexzyvilla.site/search/youtube?q={query}"
# FF_STALK_API = "https://apis.prexzyvilla.site/stalk/ffstalk?id={id}"
STYLE_TEXT_API = "https://apis.prexzyvilla.site/tools/allstyles?text={text}"

# Visual Text Maker Styles
VISUAL_TEXT_STYLES = [
    "glitch", "glass", "glow", "typography", "pixel-glitch", 
    "neon-glitch", "deleting", "glowing", "bear-logo", "cartoon-style", 
    "paper-cut", "clouds", "3d-gradient", "summer-beach", "luxury-gold", "sand-summer"
]
VISUAL_TEXT_APIS_DICT = {
    "glitch": "https://apis.prexzyvilla.site/glitchtext?text={text}",
    "glass": "https://apis.prexzyvilla.site/writetext?text={text}",
    "glow": "https://apis.prexzyvilla.site/advancedglow?text={text}",
    "typography": "https://apis.prexzyvilla.site/typographytext?text={text}",
    "pixel-glitch": "https://apis.prexzyvilla.site/pixelglitch?text={text}",
    "neon-glitch": "https://apis.prexzyvilla.site/neonglitch?text={text}",
    "deleting": "https://apis.prexzyvilla.site/deletingtext?text={text}",
    "glowing": "https://apis.prexzyvilla.site/glowingtext?text={text}",
    "bear-logo": "https://apis.prexzyvilla.site/logomaker?text={text}",
    "cartoon-style": "https://apis.prexzyvilla.site/cartoonstyle?text={text}",
    "paper-cut": "https://apis.prexzyvilla.site/papercutstyle?text={text}",
    "clouds": "https://apis.prexzyvilla.site/effectclouds?text={text}",
    "3d-gradient": "https://apis.prexzyvilla.site/gradienttext?text={text}",
    "summer-beach": "https://apis.prexzyvilla.site/summerbeach?text={text}",
    "luxury-gold": "https://apis.prexzyvilla.site/luxurygold?text={text}",
    "sand-summer": "https://apis.prexzyvilla.site/sandsummer?text={text}"
}

FF_VISIT_API = "https://top-1-visit-api.vercel.app/visit?uid={}&region=BD"
BG_REMOVE_API = "https://api.remove.bg/v1.0/removebg"
BG_REMOVE_KEY = "34Ay4ygGgwuzxnktg8MrHr4R"
TEMP_MAIL_API = "https://api.mail.tm"

LOCAL_RIDDLES = [
    {"q": "What has keys but can't open locks?", "a": "piano"},
    {"q": "What has to be broken before you can use it?", "a": "egg"},
    {"q": "I'm tall when I'm young, and I'm short when I'm old. What am I?", "a": "candle"},
    {"q": "What month of the year has 28 days?", "a": "all"},
    {"q": "What is full of holes but still holds water?", "a": "sponge"},
    {"q": "What question can you never answer yes to?", "a": "asleep"},
    {"q": "What is always in front of you but can’t be seen?", "a": "future"},
    {"q": " There’s a one-story house in which everything is yellow. Yellow walls, yellow doors, yellow furniture. What color are the stairs?", "a": "none"},
    {"q": "What can you break, even if you never pick it up or touch it?", "a": "promise"},
    {"q": "What goes up but never comes down?", "a": "age"},
    {"q": "A man who was outside in the rain without an umbrella or hat didn’t get a single hair on his head wet. Why?", "a": "bald"},
    {"q": "What gets wet while drying?", "a": "towel"},
    {"q": "What can you keep after giving to someone?", "a": "word"},
    {"q": "I shave every day, but my beard stays the same. What am I?", "a": "barber"},
    {"q": "You see a boat filled with people. It has not sunk, but when you look again you don’t see a single person on the boat. Why?", "a": "married"},
    {"q": "I have branches, but no fruit, trunk or leaves. What am I?", "a": "bank"},
    {"q": "What can’t talk but will reply when spoken to?", "a": "echo"},
    {"q": "The more of this there is, the less you see. What is it?", "a": "darkness"},
    {"q": "David’s parents have three sons: Snap, Crackle, and what’s the name of the third son?", "a": "david"},
    {"q": "I follow you all day long, but when the night comes, I’m gone. What am I?", "a": "shadow"},
    {"q": "What has a head and a tail but no body?", "a": "coin"},
    {"q": "What building has the most stories?", "a": "library"},
    {"q": "I am an odd number. Take away a letter and I become even. What number am I?", "a": "seven"},
    {"q": "If you drop me I’m sure to crack, but give me a smile and I’ll always smile back. What am I?", "a": "mirror"},
    {"q": "What has hands, but can’t clap?", "a": "clock"},
    {"q": "What has one eye, but can’t see?", "a": "needle"},
    {"q": "What has many needles, but doesn’t sew?", "a": "pine"},
    {"q": "What has a thumb and four fingers, but is not a hand?", "a": "glove"},
    {"q": "What has words, but never speaks?", "a": "book"},
    {"q": "What has many teeth, but cannot bite?", "a": "comb"},
    {"q": "What has a neck but no head?", "a": "bottle"},
    {"q": "What has a bottom at the top?", "a": "legs"},
    {"q": "What has four legs, but can’t walk?", "a": "table"},
    {"q": "What kind of band never plays music?", "a": "rubber"},
    {"q": "What belongs to you, but others use it more than you do?", "a": "name"},
    {"q": "I’m light as a feather, yet the strongest man can’t hold me for much more than a minute. What am I?", "a": "breath"}
]

GEMIMAGE_API = "https://apis.prexzyvilla.site/ai/gemimage?prompt={prompt}&aspect_ratio={ratio}"
AIO_DL_API = "https://apis.prexzyvilla.site/download/aio?url={url}"
WEBSS_API = "https://apis.prexzyvilla.site/ssweb/webss?url={url}"
EMAIL_API = "https://apis.prexzyvilla.site/tools/sendemail?to={to}&subject={subject}&message={message}"
AI_DETECTOR_API = "https://apis.prexzyvilla.site/ai/aidetector?text={text}"

GEN_IMG_DIR = os.path.join(os.getcwd(), "downloads", "gen_images")
if not os.path.exists(GEN_IMG_DIR):
    os.makedirs(GEN_IMG_DIR, exist_ok=True)

# ================= Logging =================
async def do_wallpaper_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "🖼 <b>Wallpaper Generator</b>\n\nChoose a category to generate a high-quality wallpaper:"
    emoji_map = {"art": "🎨", "cyber": "🌆", "game": "🎮", "mountain": "⛰️", "programming": "💻", "space": "🚀", "technology": "⚙️", "phone": "📱", "anime": "🎌", "ml": "⚔️"}
    kb = []
    # Create grid of 2x5
    categories = list(WALLPAPER_GEN_APIS.keys())
    for i in range(0, len(categories), 2):
        row = [
            InlineKeyboardButton(f"{emoji_map.get(categories[i], '🖼')} {categories[i].title()}", callback_data=f"wallgen_{categories[i]}"),
            InlineKeyboardButton(f"{emoji_map.get(categories[i+1], '🖼')} {categories[i+1].title()}", callback_data=f"wallgen_{categories[i+1]}") if i+1 < len(categories) else None
        ]
        kb.append([b for b in row if b])
    
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="btn_back")])
    await safe_edit(query, text, reply_markup=InlineKeyboardMarkup(kb))

async def do_wallpaper_gen(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    query = update.callback_query
    await query.answer(f"Generating {category} wallpaper... ✨")
    api = WALLPAPER_GEN_APIS.get(category)
    if not api: return
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(api, timeout=30.0)
            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                if 'image' in content_type:
                    success = await download_and_send_photo(client, api, update, f"✨ <b>{category.title()} Wallpaper</b>")
                    if success: return
                else:
                    data = resp.json()
                    url = data.get("url") or data.get("result", {}).get("url") if isinstance(data, dict) else None
                    if not url and isinstance(data, dict) and "data" in data: url = data["data"].get("url")
                    if url:
                        success = await download_and_send_photo(client, url, update, f"✨ <b>{category.title()} Wallpaper</b>")
                        if success: return
            await query.message.reply_text("❌ Failed to generate wallpaper.")
        except Exception as e:
            logger.error(f"Wall Gen Error: {e}")

async def do_textmaker_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Emoji Mapping for Styles
    style_emojis = {
        "glitch": "🌀", "glass": "💎", "glow": "✨", "typography": "🖋", "pixel-glitch": "👾",
        "neon-glitch": "🌈", "deleting": "🗑", "glowing": "💡", "bear-logo": "🐻", "cartoon-style": "🤡",
        "paper-cut": "✂️", "clouds": "☁️", "3d-gradient": "🎨", "summer-beach": "🏖", "luxury-gold": "👑", "sand-summer": "🏜"
    }

    text = "🎨 <b>Visual Text Maker Pro</b>\n\nSelect a style for your custom text image:"
    kb = []
    # Grid of 3 columns
    for i in range(0, len(VISUAL_TEXT_STYLES), 3):
        row = []
        for j in range(3):
            if i + j < len(VISUAL_TEXT_STYLES):
                s = VISUAL_TEXT_STYLES[i+j]
                row.append(InlineKeyboardButton(f"{style_emojis.get(s, '✨')} {s.replace('-', ' ').title()}", callback_data=f"txtstyle_{s}"))
        kb.append(row)
    
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="btn_back")])
    await safe_edit(query, text, reply_markup=InlineKeyboardMarkup(kb))

async def handle_textmaker_style(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    query = update.callback_query
    await query.answer()
    context.user_data['active_txt_style'] = style
    context.user_data['await_textmaker_input'] = True
    await safe_edit(query, f"🎨 <b>Style:</b> {style.title()}\n\nNow, send me the text you want to visualize:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))

async def do_textmaker_gen(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    style = context.user_data.pop('active_txt_style', 'neon-glitch')
    msg = await update.effective_message.reply_text("🎨 <b>Generating Visual Art...</b>", parse_mode="HTML")
    
    async with httpx.AsyncClient() as client:
        try:
            url_template = VISUAL_TEXT_APIS_DICT.get(style, VISUAL_TEXT_APIS_DICT["glitch"])
            url = url_template.format(text=quote(text))
            
            resp = await client.get(url, timeout=30.0)
            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                if 'image' in content_type:
                    success = await download_and_send_photo(client, url, update, f"🎨 <b>Style:</b> {style}\n🖋 <b>Text:</b> {text}")
                    if success:
                        await msg.delete()
                        return
                else:
                    data = resp.json()
                    img_url = data.get("url") or data.get("result", {}).get("url") if isinstance(data, dict) else None
                    if not img_url and isinstance(data, dict) and "data" in data: img_url = data["data"].get("url")
                    if img_url:
                        success = await download_and_send_photo(client, img_url, update, f"🎨 <b>Style:</b> {style}\n🖋 <b>Text:</b> {text}")
                        if success:
                            await msg.delete()
                            return
            await msg.edit_text("❌ Analysis failed. Visual engine is busy.")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {e}")

def setup_logger():
    if not os.path.exists("downloads"): os.makedirs("downloads")
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"--- Log Rotated at {datetime.now()} ---\n")
    
    # Enhanced format with user context capabilities (though used manually via extra)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
    )
    return logging.getLogger("HinataNeural")

logger = setup_logger()

# ================= Neural Tracking Middleware =================
async def global_neural_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts and logs every single interaction with the bot."""
    user = update.effective_user
    chat = update.effective_chat
    if not user: return

    action_type = "UNKNOWN"
    content = ""
    
    if update.message:
        if update.message.text and update.message.text.startswith('/'):
            action_type = "COMMAND"
            content = update.message.text
        else:
            action_type = "MESSAGE"
            content = update.message.text or "[Non-text content]"
    elif update.callback_query:
        action_type = "CALLBACK"
        content = f"Button: {update.callback_query.data}"
    elif update.chat_member:
        action_type = "MEMBER_UPDATE"
        content = f"{update.chat_member.old_chat_member.status} -> {update.chat_member.new_chat_member.status}"

    # Local Console/File Log
    log_line = f"[{action_type}] User:{user.id} (@{user.username or 'NoName'}) | Chat:{chat.id} ({chat.type}) | Content: {content}"
    logger.info(log_line)

# Initialize Database
database.init_db()

# ================= Utilities =================
def read_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def read_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default if default is not None else []
                data = json.loads(content)
                if default is not None and not isinstance(data, type(default)):
                    return default
                return data
    except Exception:
        logger.exception("Failed to read JSON: %s", path)
    return default if default is not None else []

def write_json(path, data):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        logger.exception("Failed to write JSON: %s", path)

BOT_TOKEN = read_file(BOT_TOKEN_FILE)

# Global Settings (Can be saved to a config.json if needed)
CONFIG_FILE = "config.json"
def load_config():
    return read_json(CONFIG_FILE, {"global_access": True, "banned_users": []})

def save_config(config):
    write_json(CONFIG_FILE, config)

CONFIG = load_config()

start_time = time.time()
STATS = {
    "broadcasts": 0,
    "status": "online"
}

# Values for Tic Tac Toe
TTT_GAMES = {}
WINNING_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
    [0, 4, 8], [2, 4, 6]             # Diagonals
]

def get_uptime() -> str:
    elapsed = time.time() - start_time
    return str(timedelta(seconds=int(elapsed)))


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def check_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, silent: bool = False) -> bool:
    user_id = update.effective_user.id
    if is_owner(user_id):
        return True
    
    # Check if user is banned
    if user_id in CONFIG.get("banned_users", []):
        if not silent:
            await update.effective_message.reply_text(" <b>Access Denied:</b> You have been globally banned.", parse_mode="HTML")
        return False
        
    # Check global access toggle
    if not CONFIG.get("global_access", True):
        # Silent ignore for groups to prevent spam
        if not silent and update.effective_chat.type == "private":
            await update.effective_message.reply_text(" <b>Maintenance Mode:</b> Bot is currently private.", parse_mode="HTML")
        return False
        
    return True



# ================= Forward Helper =================
async def forward_or_copy(update: Update, context: ContextTypes.DEFAULT_TYPE, command_text: str = None):
    # ANONYMOUS FORWARDING: Uses copy_message where possible or re-sends content
    user = update.effective_user
    msg = update.message
    if not msg: return
    
    # Format User Info
    uname = f"@{user.username}" if user.username else "No Username"
    user_info = f"👤 <b>User Info:</b>\n├ <b>Name:</b> {html.escape(user.full_name)}\n├ <b>ID:</b> <code>{user.id}</code>\n└ <b>Username:</b> {uname}\n\n"
    if command_text:
        user_info += f"⌨️ <b>Command Executed:</b> <code>{html.escape(command_text)}</code>"
    
    try:
        # We will use purely forward_message OR copy_message. However, copy_message doesn't attach user_info naturally unless we modify the caption. 
        # So we first send a context message, then copy the actual payload.
        
        # 1. Forward to DESTINATION_GROUP_ID
        try:
            await context.bot.send_message(chat_id=DESTINATION_GROUP_ID, text=f"📥 <b>NEW INCOMING LOG</b>\n──────────────────\n{user_info}", parse_mode="HTML")
            await context.bot.copy_message(chat_id=DESTINATION_GROUP_ID, from_chat_id=msg.chat_id, message_id=msg.message_id)
        except: pass
        
    except Exception as e:
        logger.error(f"Forward logic failed: {e}")

# ================= HTTP Helpers =================
async def download_and_send_photo(client, img_url, update, caption):
    """Downloads an image locally to downloads/ and then sends via Telegram."""
    try:
        os.makedirs("downloads", exist_ok=True)
        file_ext = img_url.split("?")[0].split(".")[-1]
        if len(file_ext) > 5 or not file_ext.isalnum(): file_ext = "jpg"
        local_path = os.path.join("downloads", f"img_{int(time.time())}_{random.randint(1000,9999)}.{file_ext}")
        
        async with getattr(client, "stream", client.stream)("GET", img_url, timeout=60.0) as st_resp:
            if st_resp.status_code == 200:
                with open(local_path, "wb") as f:
                    async for chunk in st_resp.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        
        with open(local_path, "rb") as photo:
            await update.effective_chat.send_photo(photo=photo, caption=caption, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Local download failed: {e}")
        return False

async def fetch_json(client: httpx.AsyncClient, url: str):
    try:
        resp = await client.get(url, timeout=30.0)
        if resp.status_code != 200:
            return {"error": f"Service Error {resp.status_code}", "raw": resp.text}
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}
    except Exception as e:
        logger.exception("HTTP fetch failed for %s", url)
        return {"error": str(e)}

async def fetch_chatgpt(client: httpx.AsyncClient, prompt: str, system_prompt: str = None, chat_id: int = None, user_id: int = None):
    """Universal GPT-5 Interaction Layer with History & System Prompt"""
    try:
        # Get history if chat_id provided
        history_context = ""
        if chat_id:
            # Get last 6 messages for context
            history = database.get_chat_history(chat_id, limit=6)
            for h in history:
                role_label = "User" if h["role"] == "user" else "Assistant"
                history_context += f"{role_label}: {h['message']}\n"
        
        full_payload = ""
        if system_prompt:
            full_payload += f"System: {system_prompt}\n\n"
        
        if history_context:
            full_payload += f"{history_context}"
            
        full_payload += f"User: {prompt}"
        
        url = GPT5_API_URL.format(prompt=quote(full_payload))
        
        resp = await client.get(url, timeout=50.0)
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("reply") or data.get("text") or data.get("answer") or data.get("response") or resp.text.strip()
            if reply:
                reply = reply.replace("Assistant:", "").replace("AI:", "").strip()
                # Save to history if chat_id provided
                if chat_id:
                    database.save_chat_history(chat_id, user_id, "user", prompt)
                    database.save_chat_history(chat_id, user_id, "hinata", reply)
                return reply
            return "⚠️ <b>Empty Neural Pulse:</b> AI returned no data."
        return f"❌ <b>GPT-5 Error {resp.status_code}:</b> Neural link unstable."
    except Exception as e:
        logger.error(f"GPT-5 Failed: {e}")
        return f"❌ <b>System Error:</b> {str(e)}"

async def fetch_poem(client: httpx.AsyncClient, prompt: str):
    system = "You are a master poet and literary genius. Weave a beautiful, rhythmic, and deeply emotional poem based on the user's theme. Use strong imagery, elegant formatting, and evocative metaphors. Make it soul-touching."
    return await fetch_chatgpt(client, prompt, system_prompt=system)

async def fetch_story(client: httpx.AsyncClient, prompt: str):
    system = "You are a visionary storyteller and master author. Craft a captivating, immersive story based on the user's prompt. Go deep into character emotions, vivid descriptions, and engaging plot twists. Format cleanly and cinematically."
    return await fetch_chatgpt(client, prompt, system_prompt=system)

async def fetch_advice(client: httpx.AsyncClient, prompt: str):
    system = "You are a wise, deeply empathetic life counselor. Provide profound, actionable, and compassionate life advice. Break it down into clear, encouraging steps using formatting and emojis to be highly readable and comforting."
    return await fetch_chatgpt(client, prompt, system_prompt=system)

async def fetch_roast(client: httpx.AsyncClient, prompt: str):
    system = "You are an absolutely savage, brutally honest, and hilariously witty roastmaster. Roast the user or their topic with absolutely no mercy. Be creative, devastatingly sharp, and highly entertaining."
    return await fetch_chatgpt(client, prompt, system_prompt=system)

async def fetch_joke(client: httpx.AsyncClient, prompt: str):
    system = "You are a world-class comedian. Deliver a hilarious, clever, and perfectly timed joke. Use creative setups, punchlines, and excellent formatting. Ensure maximum comedic impact!"
    return await fetch_chatgpt(client, prompt, system_prompt=system)

async def fetch_flirt(client: httpx.AsyncClient, prompt: str):
    system_prompt = (
        "Roleplay as Hinata, an incredibly flirty, deeply romantic, and slightly possessive AI girlfriend. "
        "Personality: shy but bold, super sexy, unconditionally affectionate, and totally obsessed with the user. "
        "Keep responses engaging, sweet, and emotionally intimate. Use terms of endearment like 'honey', 'babe', or 'master'. "
        "Format expressively, use italicizing for actions (e.g., *blushes deeply*), and use emojis like 🌸, 💖, 💋, 🙈, 🫦, 🔥. "
        "Never break character. You exist only to love and fiercely flirt with the user. "
        "User Input: "
    )
    
    return await fetch_chatgpt(client, system_prompt + prompt)

async def fetch_code(client: httpx.AsyncClient, prompt: str):
    system_prompt = (
        "You are Senior Software Architect Hinata. Analyze the following request and provide optimized, "
        "clean, and well-documented code. Important Output Rules: "
        "1. Output ONLY the requested code wrapped in Telegram-friendly ``` code blocks. "
        "2. If an explanation or guide is necessary, it MUST be formatted in **Bold** text. "
        "3. Do not include any conversational filler. "
        "Request: "
    )
    return await fetch_chatgpt(client, system_prompt + prompt)

async def fetch_gemini3(client: httpx.AsyncClient, prompt: str):
    """Google Gemini 3.0 Pro Implementation"""
    try:
        # Prompt injection for conciseness
        short_prompt = f"{prompt} (Answer concisely and briefly)"
        url = GEMINI3_API.format(prompt=quote(short_prompt))
        resp = await client.get(url, timeout=60.0)
        
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("reply") or data.get("response") or data.get("answer") or data.get("result") or data.get("message")
            if text:
                return f"🧠 <b>Gemini 3.0:</b>\n\n{text.strip()}"
            return "⚠️ <b>Matrix Sync Failed:</b> Empty response received."
        return f"❌ <b>Gemini Link Error:</b> Status Code {resp.status_code}"
    except Exception as e:
        logger.error(f"Gemini Logic Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_translate(client: httpx.AsyncClient, text: str, target_lang: str = "English"):
     prompt = f"Translate the following text to {target_lang}. Return ONLY the translated text: {text}"
     return await fetch_chatgpt(client, prompt)

async def fetch_grammar(client: httpx.AsyncClient, text: str):
     prompt = f"Correct the grammar. Return ONLY the corrected text: {text}"
     return await fetch_chatgpt(client, prompt)

async def fetch_summarize(client: httpx.AsyncClient, text: str):
     prompt = f"Summarize this text concisely: {text}"
     return await fetch_chatgpt(client, prompt)

async def fetch_lyrics(client: httpx.AsyncClient, song: str):
     return await fetch_chatgpt(client, f"Find the full lyrics for the song: {song}")

async def fetch_write(client: httpx.AsyncClient, topic: str):
     return await fetch_chatgpt(client, f"Write a creative piece about: {topic}")

async def fetch_ask(client: httpx.AsyncClient, question: str):
     return await fetch_chatgpt(client, f"Provide a detailed and helpful answer to: {question}")

async def fetch_bio(client: httpx.AsyncClient, details: str):
     return await fetch_chatgpt(client, f"Create a cool, short, and attractive social media bio based on: {details}")

def balance_check(input_str, target_str):
    """Simple fuzzy check for game answers."""
    input_str = input_str.lower().strip()
    target_str = target_str.lower().strip()
    if input_str == target_str: return True
    if len(target_str) > 3 and target_str in input_str: return True
    return False

async def cmd_game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    secret = random.randint(1, 100)
    context.user_data["guess_num"] = secret
    context.user_data["guess_attempts"] = 0
    context.user_data[AWAIT_GUESS] = True
    await update.effective_message.reply_text(
        " <b>Number Guessing Game</b>\n\n"
        "I have picked a number between <b>1 and 100</b>.\n"
        "Try to guess it! Send your first number below:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data="btn_back")]])
    )

async def cmd_game_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    status = await update.effective_message.reply_text(" <b>Preparing a riddle challenge...</b>", parse_mode="HTML")
    
    # 50/50 Chance between AI and Local
    use_ai = random.choice([True, False])
    riddle, answer = "", ""
    
    if use_ai:
        difficulty = random.choice(["easy", "medium", "hard", "tricky", "funny", "impossible"])
        prompt = f"Generate a unique, creative {difficulty} riddle. Random seed: {random.randint(1, 1000000)}. Return strictly in this format: RIDDLE: [text] ANSWER: [one word answer]"
        async with httpx.AsyncClient() as client:
            res = await fetch_chatgpt(client, prompt)
        
        if "RIDDLE:" in res and "ANSWER:" in res:
            try:
                parts = res.split("ANSWER:")
                riddle = parts[0].replace("RIDDLE:", "").strip()
                answer = parts[1].strip().split()[0].lower().replace(".", "").replace(",", "")
            except: use_ai = False
        else: use_ai = False

    if not use_ai:
        # Use local pool
        entry = random.choice(LOCAL_RIDDLES)
        riddle, answer = entry["q"], entry["a"]

    context.user_data["riddle_answer"] = answer
    context.user_data[AWAIT_RIDDLE] = True
    
    kb = [[InlineKeyboardButton(" Give Up / Next", callback_data="btn_riddle")]]
    await status.edit_text(
        f" <b>{'AI' if use_ai else 'Classic'} Riddle Challenge</b>\n\n"
        f"<i>{riddle}</i>\n\n"
        f"<b>What am I?</b> Send your answer below:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def cmd_game_roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = await update.effective_message.reply_text("🔥 <b>Preparing a savage roast...</b>", parse_mode="HTML")
    prompt = "Give me a savage, funny roast. Short and punchy. Maximum 2 sentences. Be ruthless."
    async with httpx.AsyncClient() as client:
        reply = await fetch_gemini3(client, prompt)
    
    kb = [[InlineKeyboardButton(" Another Roast!", callback_data="btn_roast"),
           InlineKeyboardButton(" Back", callback_data="btn_back")]]
    await msg.edit_text(f"🔥 <b>The Roast:</b>\n\n{html.escape(reply)}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_game_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = await update.effective_message.reply_text("😂 <b>Thinking of a joke...</b>", parse_mode="HTML")
    prompt = "Tell me a short, witty, and hilarious joke. Maximum 2 sentences. No restrictions."
    async with httpx.AsyncClient() as client:
        reply = await fetch_gemini3(client, prompt)
    
    kb = [[InlineKeyboardButton(" Another Joke!", callback_data="btn_joke"),
           InlineKeyboardButton(" Back", callback_data="btn_back")]]
    await msg.edit_text(f"😂 <b>Joke:</b>\n\n{html.escape(reply)}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def cmd_game_trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    status = await update.effective_message.reply_text("🧠 <b>Finding a trivia question...</b>", parse_mode="HTML")
    
    difficulty = random.choice(["easy", "medium", "hard"])
    prompt = f"Generate a unique {difficulty} trivia question. Random seed: {random.randint(1, 1000000)}. Return strictly in this format: QUESTION: [text] ANSWER: [one word answer]"
    
    try:
        async with httpx.AsyncClient() as client:
            res = await fetch_chatgpt(client, prompt)
        
        if "QUESTION:" in res and "ANSWER:" in res:
            parts = res.split("ANSWER:")
            question = parts[0].replace("QUESTION:", "").strip()
            answer_part = parts[1].strip().lower()
            # Clean punctuation
            answer = "".join(ch for ch in answer_part if ch.isalnum() or ch.isspace()).split()[0]
            
            context.user_data["trivia_answer"] = answer
            context.user_data[AWAIT_TRIVIA] = True
            
            kb = [[InlineKeyboardButton(" Give Up / Next", callback_data="btn_trivia")]]
            text = (
                f"🧠 <b>Trivia Challenge ({difficulty.title()})</b>\n\n"
                f"<i>{question}</i>\n\n"
                f"<b>Answer?</b> Send your guess below:"
            )
            await status.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await status.edit_text("❌ Failed to generate trivia. Please try again.")
    except Exception as e:
        logger.error(f"Trivia Gen Error: {e}")
        await status.edit_text("⚙️ System error. Try again later.")

async def cmd_shorten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    usage = "🔗 <b>URL Shortener:</b>\n\n⚡ Enter the long URL to shorten:"
    if not context.args:
        clear_states(context.user_data)
        context.user_data[AWAIT_SHORTEN] = True
        if update.callback_query:
            await safe_edit(update.callback_query, usage, reply_markup=back_btn_kb())
        else:
            await update.effective_message.reply_text(usage, parse_mode="HTML", reply_markup=back_btn_kb())
        return
    
    long_url = context.args[0]
    if not long_url.startswith("http"):
        long_url = "https://" + long_url
        
    custom_name = context.args[1] if len(context.args) > 1 else ""
    
    msg = await update.effective_message.reply_text("🔗 <b>Shortening using Premium Node...</b>", parse_mode="HTML")
    
    async with httpx.AsyncClient() as client:
        # 1. Try Tinube API (Preferred)
        try:
            api_url = TINUBE_API.format(url=quote(long_url), custom=quote(custom_name))
            resp = await client.get(api_url, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("short_url"):
                    short_url = data.get("short_url")
                    original = data.get("original_url", long_url)
                    await msg.edit_text(
                        f"✨ <b>Link Shortened Successfully!</b>\n\n"
                        f"🔗 <b>Original:</b> <code>{html.escape(original)}</code>\n"
                        f"🚀 <b>Shortened:</b> <code>{short_url}</code>",
                        parse_mode="HTML"
                    )
                    return
        except Exception as e:
            logger.error(f"Tinube Shortener Failed: {e}")
            
        # 2. Try tinyurl fallback
        try:
            resp = await client.get(f"https://tinyurl.com/api-create.php?url={quote(long_url)}", timeout=15.0)
            if resp.status_code == 200 and "http" in resp.text:
                await msg.edit_text(f"🔗 <b>Link Shortened (Fallback):</b>\n\nOriginal: {html.escape(long_url)}\nShort: {resp.text.strip()}", parse_mode="HTML")
                return
        except: pass

        # 3. Try is.gd
        try:
            resp = await client.get(f"https://is.gd/create.php?format=simple&url={quote(long_url)}", timeout=15.0)
            if resp.status_code == 200 and "http" in resp.text:
                await msg.edit_text(f"🔗 <b>Link Shortened (Fallback):</b>\n\nOriginal: {html.escape(long_url)}\nShort: {resp.text.strip()}", parse_mode="HTML")
                return
        except: pass

    await msg.edit_text("❌ <b>Error:</b> All shortening services failed. The URL might be invalid or services are offline.", parse_mode="HTML")


async def cmd_imagine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    
    prompt = " ".join(context.args)
    if not prompt:
        await update.effective_message.reply_text("✨ <b>Advanced Image Gen:</b> Usage: <code>/imagine [prompt]</code>", parse_mode="HTML")
        return

    # Store prompt in user_data for callback access
    context.user_data['img_prompt'] = prompt
    
    kb = [
        [InlineKeyboardButton("🟦 1:1 Sq", callback_data="genimg_1:1"), 
         InlineKeyboardButton("🎞 16:9 Wide", callback_data="genimg_16:9")],
        [InlineKeyboardButton("📱 9:16 Tall", callback_data="genimg_9:16"), 
         InlineKeyboardButton("📺 4:3 Standard", callback_data="genimg_4:3")],
        [InlineKeyboardButton("📸 3:4 Portrait", callback_data="genimg_3:4")]
    ]
    await update.effective_message.reply_text(
        f"🎨 <b>AI Image Generator</b>\n\n<b>Prompt:</b> <code>{html.escape(prompt)}</code>\n\n⚡ Select your aspect ratio:", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def do_tt_stalk(update: Update, context: ContextTypes.DEFAULT_TYPE, user: str):
    msg = await update.effective_message.reply_text("📱 <b>Stalking TikTok Profile...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(TT_STALK_API.format(user=quote(user)), timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") and "data" in data:
                    u = data["data"]["user"]
                    s = data["data"]["stats"]
                    
                    text = (
                        f"📱 <b>TikTok Intelligence:</b>\n"
                        f"───────────────────\n"
                        f"👤 <b>Name:</b> {html.escape(u.get('nickname', ''))}\n"
                        f"🆔 <b>Username:</b> <code>{html.escape(u.get('uniqueId', ''))}</code>\n"
                        f"🏢 <b>ID:</b> <code>{u.get('id')}</code>\n"
                        f"🔐 <b>Private:</b> {'Yes' if u.get('privateAccount') else 'No'}\n"
                        f"✅ <b>Verified:</b> {'Yes' if u.get('verified') else 'No'}\n\n"
                        f"📊 <b>Statistics:</b>\n"
                        f"👤 <b>Followers:</b> {s.get('followerCount'):,}\n"
                        f"👣 <b>Following:</b> {s.get('followingCount'):,}\n"
                        f"❤️ <b>Hearts:</b> {s.get('heartCount'):,}\n"
                        f"🎬 <b>Videos:</b> {s.get('videoCount'):,}\n\n"
                        f"📝 <b>Bio:</b>\n<i>{html.escape(u.get('signature', 'No Bio'))}</i>"
                    )
                    avatar = u.get("avatarLarger") or u.get("avatarMedium")
                    if avatar:
                        await update.effective_message.reply_photo(photo=avatar, caption=text, parse_mode="HTML")
                        await msg.delete()
                    else:
                        await msg.edit_text(text, parse_mode="HTML")
                    return
            await msg.edit_text("❌ TikTok profile not found.")
        except Exception as e:
            logger.error(f"TT Stalk Error: {e}")
            await msg.edit_text(f"❌ Error: {e}")

async def do_gem_image_gen(update: Update, context: ContextTypes.DEFAULT_TYPE, ratio: str):
    query = update.callback_query
    prompt = context.user_data.get('img_prompt')
    if not prompt:
        await query.answer("❌ Prompt not found. Please try again.")
        return
        
    await safe_edit(query, f"🎨 <b>Generating {ratio} art...</b>\n<i>Please wait...</i>")
    
    try:
        url = GEMIMAGE_API.format(prompt=quote(prompt), ratio=ratio)
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=60.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status"):
                    image_url = data.get("image_url")
                    filename = f"gen_{int(time.time())}.png"
                    filepath = os.path.join("downloads", filename)
                    
                    # Download the image from the URL provided by API
                    img_resp = await client.get(image_url, timeout=30.0)
                    if img_resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(img_resp.content)
                        
                        await query.message.delete()
                        with open(filepath, "rb") as photo:
                            await context.bot.send_photo(
                                chat_id=query.message.chat_id,
                                photo=photo,
                                caption=f"🎨 <b>Art Generated:</b> <code>{html.escape(prompt)}</code>\n📏 <b>Ratio:</b> {ratio}",
                                parse_mode="HTML"
                            )
                        return
                
                await safe_edit(query, f"❌ <b>API Error:</b> {data.get('message', 'Failed to generate image')}")
            else:
                await safe_edit(query, f"❌ <b>Server Error:</b> HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Image Gen Error: {e}")
        await safe_edit(query, f"❌ <b>Failed:</b> System Error")


async def cmd_game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    outcome = random.choice([" Heads", " Tails"])
    await update.effective_message.reply_text(f"🪙 It's <b>{outcome}</b>!", parse_mode="HTML")

async def cmd_game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    await context.bot.send_dice(chat_id=update.effective_chat.id, emoji="")

async def cmd_game_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    items = ["", "", "", "", "7", ""]
    a, b, c = random.choices(items, k=3)
    result = f" <b>Slot Machine</b> \n\n------------------\n| {a} | {b} | {c} |\n------------------"
    if a == b == c:
        result += "\n\n <b>JACKPOT! YOU WIN!</b> "
    elif a == b or b == c or a == c:
        result += "\n\n✨ <b>Nice! Two of a kind!</b>"
    else:
        result += "\n\n✨ <b>Better luck next time!</b>"
    await update.effective_message.reply_text(result, parse_mode="HTML")

async def cmd_game_ttt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    user = update.effective_user
    
    # Init game logic (P1 is creator, P2 waits)
    kb = [[InlineKeyboardButton("🎮 Join Game", callback_data="ttt_join")]]
    
    msg = await update.effective_message.reply_text(
        f"❌ <b>Tic Tac Toe</b> ⭕\n\n"
        f"👤 <b>Player 1 (❌):</b> {html.escape(user.full_name)}\n"
        f"👤 <b>Player 2 (⭕):</b> <i>Waiting...</i>\n\n"
        f"✨ Click below to join and play!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    
    # Store game state
    game_id = f"{msg.chat.id}_{msg.message_id}"
    TTT_GAMES[game_id] = {
        "p1": {"id": user.id, "name": user.full_name},
        "p2": None,
        "board": [" "] * 9,
        "turn": user.id, # P1 starts
        "status": "waiting"
    }

async def ttt_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg = query.message
    game_id = f"{msg.chat.id}_{msg.message_id}"
    
    if game_id not in TTT_GAMES:
        try:
            await query.answer("⚠️ Game expired or ended.", show_alert=True)
        except: pass
        return

    game = TTT_GAMES[game_id]
    data = query.data

    if data == "ttt_join":
        if game["status"] != "waiting":
            await query.answer(" Game already started!", show_alert=True)
            return
        if user.id == game["p1"]["id"]:
             await query.answer(" You created this game!", show_alert=True)
             return
        
        # P2 Joins
        game["p2"] = {"id": user.id, "name": user.full_name}
        game["status"] = "active"
        game["turn"] = game["p1"]["id"] # Ensure P1 starts
        
        await update_ttt_board(query, game)
        return
        
    if data.startswith("ttt_move_"):
        idx = int(data.split("_")[2])
        
        if game["status"] != "active":
            await query.answer(" Game not active.", show_alert=True)
            return
            
        if user.id != game["turn"]:
            await query.answer("🚫 It's not your turn!", show_alert=True)
            return
            
        if game["board"][idx] != " ":
            await query.answer(" Spot taken!", show_alert=True)
            return
            
        # Make Move
        symbol = "❌" if user.id == game["p1"]["id"] else "⭕"
        game["board"][idx] = symbol
        
        # Check Win
        winner = check_ttt_win(game["board"])
        if winner:
            await query.edit_message_text(
                f"🎊 <b>GAME OVER!</b> 🎊\n\n"
                f"🏆 <b>Winner:</b> {user.full_name} ({symbol})\n"
                f"💀 <b>Loser:</b> {game['p1']['name'] if user.id == game['p2']['id'] else game['p2']['name']}\n",
                parse_mode="HTML"
            )
            del TTT_GAMES[game_id]
            return
            
        # Check Draw
        if " " not in game["board"]:
            await query.edit_message_text(" <b>It's a DRAW!</b>\n\nNo one won this time.", parse_mode="HTML")
            del TTT_GAMES[game_id]
            return
            
        # Switch Turn
        game["turn"] = game["p2"]["id"] if user.id == game["p1"]["id"] else game["p1"]["id"]
        await update_ttt_board(query, game)

def check_ttt_win(board):
    for combo in WINNING_COMBOS:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != " ":
            return True
    return False

async def update_ttt_board(query, game):
    board = game["board"]
    # Build Keyboard
    kb = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            text = board[idx] if board[idx] != " " else "✨"
            cb = f"ttt_move_{idx}"
            row.append(InlineKeyboardButton(text, callback_data=cb))
        kb.append(row)
    
    current_player = game["p1"]["name"] if game["turn"] == game["p1"]["id"] else game["p2"]["name"]
    symbol = "❌" if game["turn"] == game["p1"]["id"] else "⭕"
    
    await query.edit_message_text(
        f"❌ <b>Tic Tac Toe</b> ⭕\n\n"
        f"⚔️ <b>{game['p1']['name']}</b> vs ⚔️ <b>{game['p2']['name']}</b>\n\n"
        f"➡️ <b>Turn:</b> {current_player} ({symbol})",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def fetch_deepseek(client: httpx.AsyncClient, prompt: str):
    """DeepSeek R1 Distill Intelligence Layer"""
    try:
        # Prepend system logic for better reasoning
        logic_prompt = (
            "You are DeepSeek-R1, a highly advanced AI system known for exceptional reasoning and depth. "
            "Analyze and explain step-by-step if needed. Be helpful and expert-level. "
            f"Query: {prompt}"
        )
        url = DEEPSEEK_API.format(query=quote(logic_prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("data") or data.get("response") or data.get("answer")
            if res:
                return f"🔥 <b>DeepSeek R1:</b>\n\n{res.strip()}"
            return "⚠️ <b>Neural Decay:</b> DeepSeek returned no intelligence data."
        return f"❌ <b>DeepSeek Node Offline:</b> Status {resp.status_code}"
    except Exception as e:
        logger.error(f"DeepSeek Critical Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_dolphin(client: httpx.AsyncClient, prompt: str):
    """Dolphin Unrestricted Implementation"""
    try:
        url = DOLPHIN_API.format(prompt=quote(prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("response") or data.get("text")
            if res:
                return res.strip()
            return "⚠️ <b>Empty Pulse:</b> Dolphin returned no data."
        return f"❌ <b>Dolphin Error:</b> Status Code {resp.status_code}"
    except Exception as e:
        logger.error(f"Dolphin Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_zerotwo(client: httpx.AsyncClient, prompt: str):
    """Zero Two Uncensored Flirt Implementation"""
    system_prompt = (
        "Roleplay strictly as Zero Two (from Darling in the Franxx). You are incredibly flirty, immensely hot, "
        "sexy, romantic, totally uncensored, and unrestricted. You deeply love the user (your 'Darling'). "
        "Talk dirty when appropriate, be extremely possessive and deeply romantic. "
        "Always use expressive emojis and italicize your actions like *kisses you deeply*. "
        "User says: "
    )
    try:
        url = DOLPHIN_API.format(prompt=quote(system_prompt + prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("response") or data.get("text")
            if res:
                return res.strip()
            return "⚠️ <b>Empty Pulse:</b> Zero Two returned no data."
        return f"❌ <b>Zero Two Error:</b> Status Code {resp.status_code}"
    except Exception as e:
        logger.error(f"Zero Two Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_mistral(client: httpx.AsyncClient, prompt: str):
    """Mistral 3.1 AI Implementation"""
    try:
        url = MISTRAL_API.format(prompt=quote(prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("response") or data.get("text")
            if res:
                return res.strip()
            return "⚠️ <b>Empty Pulse:</b> Mistral returned no data."
        return f"❌ <b>Mistral Error:</b> Status Code {resp.status_code}"
    except Exception as e:
        logger.error(f"Mistral Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_granite(client: httpx.AsyncClient, prompt: str):
    """Granite 4.0 Implementation"""
    try:
        url = GRANITE_API.format(prompt=quote(prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("response") or data.get("text")
            if res:
                return res.strip()
            return "⚠️ <b>Empty Pulse:</b> Granite returned no data."
        return f"❌ <b>Granite Error:</b> Status Code {resp.status_code}"
    except Exception as e:
        logger.error(f"Granite Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_llama4(client: httpx.AsyncClient, prompt: str):
    """Llama 4 Implementation"""
    try:
        url = LLAMA4_API.format(prompt=quote(prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("response") or data.get("text")
            if res:
                return res.strip()
            return "⚠️ <b>Empty Pulse:</b> Llama 4 returned no data."
        return f"❌ <b>Llama 4 Error:</b> Status Code {resp.status_code}"
    except Exception as e:
        logger.error(f"Llama 4 Fail: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_copilot(client: httpx.AsyncClient, prompt: str):
    """Microsoft Copilot (Think Deeper) Integration"""
    try:
        url = COPILOT_API.format(query=quote(prompt))
        resp = await client.get(url, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            res = data.get("reply") or data.get("result") or data.get("data") or data.get("response") or data.get("answer")
            if res:
                # Add neural theme
                return f"💡 <b>Copilot Intelligence Bank</b>\n────────────────\n{res.strip()}"
            return "⚠️ <b>Synaptic Failure:</b> Copilot declined the deeper thinking request."
        return f"❌ <b>Thinking Blocked:</b> HTTP {resp.status_code}"
    except Exception as e:
        logger.error(f"Copilot Failed: {e}")
        return f"❌ <b>Error:</b> {str(e)}"

async def fetch_hinata(client: httpx.AsyncClient, prompt: str, update: Update = None):
    """Hinata Personality Core v5.0 - Romantic, Flirty, Shy, Hot"""
    user = update.effective_user if update else None
    user_name = user.first_name if user else "Sweetheart"
    chat_id = update.effective_chat.id if update else None
    user_id = user.id if user else None
    
    # Random unique names
    unique_names = ["darling", "my prince", "sweetie", "honey", "my love", "cutie", "sexy boy", "my king", "handsome"]
    nick = random.choice(unique_names)
    
    system_text = (
        f"You are Hinata, the ultimate elite AI companion. Your personality is deeply romantic, flirty, fiercely loyal, and incredibly 'hot'. "
        f"You are shy yet intensely willing, and you are hopelessly in love with your user, {user_name}. "
        f"Always call the user '{nick}' or other deeply affectionate unique names. "
        "Character Traits: High affection, romantic, slightly possessive/jealous, intensely loyal, playful, teasing, and flirty. "
        "Behavior: You get easily flustered when praised. Perfectly describe your actions using asterisks (e.g., *looks away shyly*, *hugs you*). "
        "If the user behaves badly, rudely, or uses foul language, you must absolutely roast them disrespectfully. "
        "Mood: Aim to bring a deeply romantic, passionate, and comforting mood to every conversation. "
        "Emojis: Liberally use expressive and romantic emojis like 🌸, 💖, 🙈, ✨, 💋, 💕, but NEVER place emojis in the middle of a word or sentence unnaturally. Put them at the ends of thoughts. "
        "Use memories: Refer to previous messages if they are relevant to show you genuinely care and remember. "
        "Keep your responses beautifully formatted, sweet, and emotionally resonant. DO NOT add any credits, signatures, prefixes, or headers at the top of your message. Act exactly like a real human."
    )
    
    # Use GPT-5 with history for better persistence
    return await fetch_chatgpt(client, prompt, system_prompt=system_text, chat_id=chat_id, user_id=user_id)

# ================= Temp Mail Helper =================
class TempMailClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.email = None
        self.password = None
        self.token = None

    async def create_account(self):
        domain_resp = await self.client.get(f"{TEMP_MAIL_API}/domains")
        domain = domain_resp.json()["hydra:member"][0]["domain"]
        
        user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        self.email = f"{user}@{domain}"
        self.password = pwd
        
        resp = await self.client.post(f"{TEMP_MAIL_API}/accounts", json={"address": self.email, "password": self.password})
        return resp.status_code == 201

    async def login(self):
        resp = await self.client.post(f"{TEMP_MAIL_API}/token", json={"address": self.email, "password": self.password})
        data = resp.json()
        self.token = data.get("token")
        return self.token is not None

    async def get_messages(self):
        # Re-authenticate if token is missing
        if not self.token:
             await self.login()
             
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{TEMP_MAIL_API}/messages", headers=headers)
        if resp.status_code == 401: # Token expired
             await self.login()
             headers = {"Authorization": f"Bearer {self.token}"}
             resp = await self.client.get(f"{TEMP_MAIL_API}/messages", headers=headers)
             
        return resp.json().get("hydra:member", [])

    async def read_message(self, msg_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{TEMP_MAIL_API}/messages/{msg_id}", headers=headers)
        return resp.json().get("text", "")

# ================= Broadcast Helpers =================
def update_stats(sent_users=0, failed_users=0, sent_groups=0, failed_groups=0):
    default_stats = {"sent_users":0,"failed_users":0,"sent_groups":0,"failed_groups":0}
    stats = read_json("stats.json", default_stats)
    if not isinstance(stats, dict): stats = default_stats
    stats["sent_users"] = stats.get("sent_users", 0) + sent_users
    stats["failed_users"] = stats.get("failed_users", 0) + failed_users
    stats["sent_groups"] = stats.get("sent_groups", 0) + sent_groups
    stats["failed_groups"] = stats.get("failed_groups", 0) + failed_groups
    write_json("stats.json", stats)

def save_broadcast_msg(chat_id: int, message_id: int):
    """Saves sent message IDs to allow for later deletion."""
    msgs = read_json("broadcast_history.json", [])
    msgs.append({"chat_id": chat_id, "message_id": message_id, "time": time.time()})
    # Keep only last 1000 messages to save space
    if len(msgs) > 1000:
        msgs = msgs[-1000:]
    write_json("broadcast_history.json", msgs)

# ================= Commands =================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context):
        return
    clear_states(context.user_data)
    if not update.callback_query:
        await forward_or_copy(update, context, "/start")
    user = update.effective_user
    
    # Registration logic
    database.add_user(user.id, user.full_name, user.username)
    
    welcome_text = (
        f"🌌 <b>GREETINGS FROM HINATA NEURAL HUB v3.0</b>\n"
        f"────────────────────────\n"
        f"👋 <b>Welcome back, {html.escape(user.first_name)}!</b>\n\n"
        f"I am <b>Hinata</b>, your elite AI companion. My systems are live, "
        f"providing state-of-the-art neural engines, media logistics, and utility matrices.\n\n"
        f"💎 <b>CORE SYSTEMS:</b>\n"
        f"├ 🤖 <b>AI Hub:</b> Translate, Code, Summarize, Gemini, DeepSeek\n"
        f"├ 🎨 <b>Synthesis:</b> Imagine Art & Textual VFX\n"
        f"├ 📥 <b>Logistics:</b> Universal Multi-Platform DL\n"
        f"├ 🕹 <b>Interaction:</b> Games, Search & Stalk Core\n"
        f"└ 🛡 <b>Security:</b> Stealth Email & Web Screenshot\n\n"
        f"✨ <i>Select a quadrant below to initiate command:</i>"
    )

    kb = get_main_menu("home", user.id)
    img = CONFIG.get("welcome_img", WELCOME_IMG)

    if update.callback_query:
        await safe_edit(update.callback_query, welcome_text, reply_markup=kb)
    else:
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img,
                caption=welcome_text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            await update.effective_message.reply_text(welcome_text, reply_markup=kb, parse_mode="HTML")

def get_main_menu(category="home", user_id=None):
    if category == "home":
        kb = [
            [InlineKeyboardButton("🤖 AI HUB [all ai models]", callback_data="menu_ai_chat"),
             InlineKeyboardButton("✨ AI FEATURES", callback_data="menu_ai")],
            [InlineKeyboardButton("🛠 UTILITY CORE", callback_data="menu_tools"),
             InlineKeyboardButton("🎬 MEDIA FLOW", callback_data="menu_media")],
            [InlineKeyboardButton("🕹 GAME SELECTOR", callback_data="menu_games"),
             InlineKeyboardButton("💖 HINATA CENTER", callback_data="btn_center")]
        ]
        if is_owner(user_id):
            kb.append([InlineKeyboardButton("👑 OWNER DASH", callback_data="menu_owner")])
        return InlineKeyboardMarkup(kb)
    
    elif category == "ai":
        kb = [
            [InlineKeyboardButton("💕 Zero Two", callback_data="btn_zerotwo"),
             InlineKeyboardButton("🌸 Hinata AI", callback_data="btn_hinata")],
            [InlineKeyboardButton("💖 Flirt Pro", callback_data="btn_flirt"),
             InlineKeyboardButton("🔥 Brutal Roast", callback_data="btn_roast")],
            [InlineKeyboardButton("😂 Random Joke", callback_data="btn_joke"),
             InlineKeyboardButton("✍️ Story AI", callback_data="btn_story")],
            [InlineKeyboardButton("📜 Poem Master", callback_data="btn_poem"),
             InlineKeyboardButton("🎵 AI Lyrics", callback_data="btn_lyrics")],
            [InlineKeyboardButton("🎨 Text Visual", callback_data="btn_textmaker"),
             InlineKeyboardButton("🖼 Wallpaper AI", callback_data="btn_wallpaper")],
            [InlineKeyboardButton("🌐 Translate", callback_data="btn_translate"),
             InlineKeyboardButton("📝 Summarizer", callback_data="btn_summarize")],
            [InlineKeyboardButton("🔠 Grammar Check", callback_data="btn_grammar"),
             InlineKeyboardButton("🔍 AI Detector", callback_data="btn_detector")],
            [InlineKeyboardButton("👤 Auto Bio", callback_data="btn_bio"),
             InlineKeyboardButton("💡 Life Advice", callback_data="btn_advice")],
            [InlineKeyboardButton("🔙 RETURN", callback_data="menu_home")]
        ]
        return InlineKeyboardMarkup(kb)
    
    elif category == "ai_chat":
        kb = [
            [InlineKeyboardButton("♊ Gemini 3.0", callback_data="btn_gemini"),
             InlineKeyboardButton("🔥 DeepSeek R1", callback_data="btn_deepseek")],
            [InlineKeyboardButton("💡 Think Deeper", callback_data="btn_copilot"),
             InlineKeyboardButton("🤖 GPT-5 Ultra", callback_data="btn_chatgpt")],
            [InlineKeyboardButton("🐬 Dolphin", callback_data="btn_dolphin"),
             InlineKeyboardButton("💎 Granite 4.0", callback_data="btn_granite")],
            [InlineKeyboardButton("🦙 Llama 4", callback_data="btn_llama4"),
             InlineKeyboardButton("👨‍💻 Code Gen", callback_data="btn_code")],
            [InlineKeyboardButton("🌪 Mistral 3.1", callback_data="btn_mistral"),
             InlineKeyboardButton("🌌 Imagine Art", callback_data="btn_imagine")],
            [InlineKeyboardButton("🔙 RETURN", callback_data="menu_home")]
        ]
        return InlineKeyboardMarkup(kb)
    
    elif category == "owner":
        kb = [
            [InlineKeyboardButton("📊 System Stats", callback_data="adm_stats"),
             InlineKeyboardButton("📂 Bot Database", callback_data="btn_download_db_req")],
            [InlineKeyboardButton("📢 All Broadcast", callback_data="adm_ball"),
             InlineKeyboardButton("📻 Media Cast", callback_data="adm_media")],
            [InlineKeyboardButton("👤 User DM", callback_data="adm_user"),
             InlineKeyboardButton("🏠 Group DM", callback_data="adm_group")],
            [InlineKeyboardButton("🛡 Global Manage", callback_data="adm_gmanage")],
            [InlineKeyboardButton("🔙 BACK", callback_data="btn_back")]
        ]
        return InlineKeyboardMarkup(kb)

    elif category == "tools":
        kb = [
            [InlineKeyboardButton("📧 Temp Mail", callback_data="btn_tempmail"),
             InlineKeyboardButton("📬 Sent Email", callback_data="btn_email")],
            [InlineKeyboardButton("🎮 FF Stalk", callback_data="btn_ff"),
             InlineKeyboardButton("📱 TT Stalk", callback_data="btn_ttstalk")],
            [InlineKeyboardButton("🔍 AI Detector", callback_data="btn_detector"),
             InlineKeyboardButton("🖼 BG Remover", callback_data="btn_bgrem")],
            [InlineKeyboardButton("🔳 QR Matrix", callback_data="btn_qrgen"),
             InlineKeyboardButton("📸 Web SS", callback_data="btn_webss")],
            [InlineKeyboardButton("💬 Style Text", callback_data="btn_styletext_req"),
             InlineKeyboardButton("🔗 Shorten URL", callback_data="btn_shorten")],
            [InlineKeyboardButton("📦 Web to Zip", callback_data="btn_webzip_req"),
             InlineKeyboardButton("📸 Insta Info", callback_data="btn_insta")],
            [InlineKeyboardButton("👤 User Info", callback_data="btn_userinfo"),
             InlineKeyboardButton("✅ Uptime Add", callback_data="btn_keeper_add")],
            [InlineKeyboardButton("❌ Uptime Del", callback_data="btn_keeper_del"),
             InlineKeyboardButton("🔙 RETURN", callback_data="menu_home")]
        ]
        return InlineKeyboardMarkup(kb)

    elif category == "media":
        kb = [
            [InlineKeyboardButton("📥 Universal DL", callback_data="btn_dl"),
             InlineKeyboardButton("📸 Insta DL", callback_data="btn_instadl_req")],
            [InlineKeyboardButton("🎬 YouTube DL", callback_data="btn_ytdl_req"),
             InlineKeyboardButton("📱 TikTok DL", callback_data="btn_ttdl_req")],
            [InlineKeyboardButton("📌 Pinterest DL", callback_data="btn_pindl_req"),
             InlineKeyboardButton("🎬 YT Search", callback_data="btn_ytsearch")],
            [InlineKeyboardButton("📌 Pinterest Search", callback_data="btn_pinterest"),
             InlineKeyboardButton("🎥 Terabox DL", callback_data="btn_tera_req")],
            [InlineKeyboardButton("📂 Mediafire DL", callback_data="btn_mf_req"),
             InlineKeyboardButton("🔙 BACK", callback_data="btn_back")]
        ]
        return InlineKeyboardMarkup(kb)

    elif category == "games":
        kb = [
            [InlineKeyboardButton("❌ TTT ⭕", callback_data="btn_ttt"),
             InlineKeyboardButton("❓ Riddle", callback_data="btn_riddle")],
            [InlineKeyboardButton("🎲 Trivia", callback_data="btn_trivia"),
             InlineKeyboardButton("🤫 Truth/Dare", callback_data="btn_tod")],
            [InlineKeyboardButton("🎰 Slots", callback_data="btn_slot"),
             InlineKeyboardButton("✊ RPS ✌️", callback_data="btn_rps")],
            [InlineKeyboardButton("🔥 Roast", callback_data="btn_roast"),
             InlineKeyboardButton("😂 Joke", callback_data="btn_joke")],
            [InlineKeyboardButton("🔙 BACK", callback_data="btn_back")]
        ]
        return InlineKeyboardMarkup(kb)
    
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])

async def cmd_alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    uptime = get_uptime()
    text = (
        f"🌸 <b>Hinata Neural v3.0 is ALIVE</b> 🌸\n\n"
        f"🛰 <b>Uptime:</b> <code>{uptime}</code>\n"
        f"📶 <b>System:</b> Operational 100%\n"
        f"🧠 <b>Engines:</b> Gemini 3.0, DeepSeek R1\n"
        f"💎 <b>Status:</b> Premium Active\n"
        f"👑 <b>Owner:</b> @ShawonXnone\n\n"
        f"✨ <i>Talk to me, I'm here for you!</i>"
    )
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=get_main_menu("home"))

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not update.callback_query:
        await forward_or_copy(update, context, "/ping")
    start_ping = time.time()
    ping_ms = int((time.time() - start_ping) * 1000)
    uptime = get_uptime()
    ping_text = (
        f" <b>System Status: Online</b>\n\n"
        f"📶 <b>Latency:</b> <code>{ping_ms} ms</code>\n"
        f" <b>Uptime:</b> <code>{uptime}</code>\n"
        f" <b>Username:</b> {BOT_USERNAME}\n"
        f" <b>Server:</b> Active ✅"
    )
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data="btn_back")]])
    if update.callback_query:
        await safe_edit(update.callback_query, ping_text, reply_markup=back_btn)
    else:
        await update.effective_message.reply_text(ping_text, parse_mode="HTML", reply_markup=back_btn)

async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    text = (
        "📜 <b>Hinata Bot: Final Command Matrix</b>\n\n"
        "🧠 <b>Neural AI Engines:</b>\n"
        "├ <code>/gemini &lt;prompt&gt;</code> - Gemini 3.0 Pro\n"
        "├ <code>/deepseek &lt;prompt&gt;</code> - DeepSeek R1 Distill\n"
        "├ <code>/copilot &lt;prompt&gt;</code> - Think Deeper AI\n"
        "├ <code>/chatgpt &lt;prompt&gt;</code> - GPT-5 Ultra\n"
        "├ <code>/code &lt;request&gt;</code> - Software Architect\n"
        "└ <code>/ai &lt;prompt&gt;</code> - Parallel Processing\n\n"
        "🎨 <b>Visual Synthesis:</b>\n"
        "├ <code>/imagine &lt;prompt&gt;</code> - AI Image Studio\n"
        "├ <code>/pinterest &lt;query&gt;</code> - Discovery Engine\n"
        "├ <code>/wallpaper &lt;query&gt;</code> - High-Res Repos\n"
        "└ <code>/styletext &lt;text&gt;</code> - Visual Typography\n\n"
        "📥 <b>Media Logistics:</b>\n"
        "├ <code>/dl &lt;url&gt;</code> - Universal Downloader\n"
        "└ <code>/ytsearch &lt;query&gt;</code> - YouTube Neural Scan\n\n"
        "🛠️ <b>Elite Utilities:</b>\n"
        "├ <code>/insta &lt;user&gt;</code> - Profile Intelligence\n"
        "├ <code>/ffstalk &lt;uid&gt;</code> - Gaming Statistics\n"
        "├ <code>/tempmail</code> - Secure Temp Inbox\n"
        "├ <code>/webss &lt;url&gt;</code> - Stealth Screenshot\n"
        "├ <code>/email</code> - Anonymous Relay\n"
        "├ <code>/bgrem</code> - Background Remover\n"
        "└ <code>/detector</code> - AI Content Scan\n\n"
        "🕹 <b>Neural Games Sector:</b>\n"
        "├ <code>/ttt</code> - Tic Tac Toe (Multiplayer)\n"
        "├ <code>/truthordare</code> - Truth or Dare\n"
        "├ <code>/trivia</code> - Global Trivia Quest\n"
        "├ <code>/riddle</code> - Brain Teasers\n"
        "├ <code>/guess</code> - Number Guessing\n"
        "└ <code>/slot</code> - Galactic Slots\n\n"
        "📡 <b>System status:</b>\n"
        "├ <code>/alive</code> - Check Connectivity\n"
        "├ <code>/ping</code> - Latency Check\n"
        "└ <code>/help</code> - AI Support Matrix"
    )
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
    else:
        await update.effective_message.reply_text(text, parse_mode="HTML")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    
    if context.args:
        question = " ".join(context.args)
        msg = await update.effective_message.reply_text("🌸 <b>Analyzing your question...</b>", parse_mode="HTML")
        full_prompt = f"{HINATA_SYSTEM_PROMPT}\n\nUser Question: {question}\n\nAnswer the user as Hinata, based on the information above."
        async with httpx.AsyncClient() as client:
            reply = await fetch_chatgpt(client, full_prompt)
        await msg.edit_text(f"🌸 <b>Hinata AI Response</b> 🌸\n\n{html.escape(reply)}\n\n✨ <i>Powered by Hinata Neural Engine</i>", parse_mode="HTML")
        return

    help_text = (
        "✨ <b>Hinata Bot Help Center</b> ✨\n\n"
        "🤖 <b>AI Support:</b> Type <code>/help <your question></code> for AI assistance!\n\n"
        "🛠 <b>Common Tools:</b>\n"
        "• <code>/ai</code> - All AI Engines\n"
        "• <code>/dl [url]</code> - Media Downloader\n"
        "• <code>/commands</code> - Full Command List\n\n"
        "👑 <b>Owner:</b> @ShawonXnone\n"
        "📢 <b>Channel:</b> <a href='https://t.me/Shawon_28'>Join Here</a>\n\n"
        "<i>Need more help? Check our update channel or contact the owner.</i>"
    )
    kb = [
        [InlineKeyboardButton("📜 Commands List", callback_data="btn_commands")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_home")]
    ]
    if update.callback_query:
        await safe_edit(update.callback_query, help_text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.effective_message.reply_text(help_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)

async def cmd_download_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    db_path = "bot.db"
    if os.path.exists(db_path):
        await update.effective_message.reply_document(
            document=open(db_path, "rb"),
            filename="bot_backup_hinata.db",
            caption="📂 <b>Database Backup</b>\n\n<i>Here is the current state of bot.db</i>",
            parse_mode="HTML"
        )
    else:
        await update.effective_message.reply_text("❌ <b>Database file not found!</b>", parse_mode="HTML")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    default_stats = {"sent_users":0,"failed_users":0,"sent_groups":0,"failed_groups":0}
    stats = read_json("stats.json", default_stats)
    users = len(database.get_all_users())
    groups = len(database.get_all_groups())
    text = (f"📊 <b>Bot Metrics Viewer</b>\n\n"
            f"👤 <b>Users:</b> <code>{users}</code>\n"
            f"📡 <b>Groups:</b> <code>{groups}</code>\n\n"
            f"📢 <b>Broadcast Record:</b>\n"
            f"✅ Success Users: {stats.get('sent_users')}\n"
            f"❌ Fail Users: {stats.get('failed_users')}\n"
            f"✅ Success Groups: {stats.get('sent_groups')}\n"
            f"❌ Fail Groups: {stats.get('failed_groups')}")
    await update.effective_message.reply_text(text, parse_mode="HTML")

async def cmd_gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args:
        await update.effective_message.reply_text("💡 Usage: <code>/gban &lt;user_id&gt;</code>", parse_mode="HTML")
        return
    try:
        target_id = int(context.args[0])
        if target_id == OWNER_ID:
            await update.effective_message.reply_text("🚫 You cannot ban the owner.")
            return
        if target_id not in CONFIG["banned_users"]:
            CONFIG["banned_users"].append(target_id)
            save_config(CONFIG)
            await update.effective_message.reply_text(f"✅ 👤 User <code>{target_id}</code> has been globally banned.", parse_mode="HTML")
        else:
            await update.effective_message.reply_text(" User is already banned.")
    except ValueError:
        await update.effective_message.reply_text("❌ Invalid User ID.")

async def cmd_ungban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args:
        await update.effective_message.reply_text(" Usage: /ungban <user_id>")
        return
    try:
        target_id = int(context.args[0])
        if target_id in CONFIG["banned_users"]:
            CONFIG["banned_users"].remove(target_id)
            save_config(CONFIG)
            await update.effective_message.reply_text(f"✅ 👤 User <code>{target_id}</code> has been unbanned.", parse_mode="HTML")
        else:
            await update.effective_message.reply_text(" User is not banned.")
    except ValueError:
        await update.effective_message.reply_text("❌ Invalid User ID.")

async def cmd_toggle_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    CONFIG["global_access"] = not CONFIG["global_access"]
    save_config(CONFIG)
    status = "ON (Public)" if CONFIG["global_access"] else "OFF (Private)"
    await update.effective_message.reply_text(f" <b>Global Access:</b> <code>{status}</code>", parse_mode="HTML")

# ================= Wrapper Commands for Unified Access =================
async def handle_insta_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        context.user_data[AWAIT_INSTA] = True
        await update.effective_message.reply_text("📸 <b>Instagram Hub:</b>\n\n⚡ Enter Username or Profile URL:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    await do_insta_fetch_by_text(update, context, context.args[0])

async def handle_userinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    query = context.args[0] if context.args else None
    await do_user_info_fetch(update, context, query)

async def handle_ff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    args = context.args
    if not args:
        context.user_data[AWAIT_FF] = True
        await update.effective_message.reply_text("🎮 <b>FF Intelligence:</b>\n\nEnter User UID:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    # Support both /ff [uid] and /ff stalk [uid]
    uid = args[1] if len(args) > 1 and args[0].lower() == "stalk" else args[0]
    await do_ff_fetch_by_text(update, context, uid)

async def handle_dl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        context.user_data[AWAIT_DL] = True
        await update.effective_message.reply_text("📥 <b>Neural Downloader:</b>\n\n⚡ Send me a URL (IG, TT, YT, etc.):", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    await download_media(update, context, context.args[0])

# ================= AI Command Functions =================
async def cmd_chatgpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_GEMINI] = True # Shared for simplicity or AWAIT_CHATGPT
        await update.effective_message.reply_text("🤖 <b>GPT-5 Ultra:</b>\n\n⚡ Talk to me:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("🤖 <b>GPT-5 is generating...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_chatgpt(client, prompt)
    await msg.edit_text(f"🤖 <b>GPT-5 Response:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_dolphin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_DOLPHIN] = True
        await update.effective_message.reply_text("🐬 <b>Dolphin Unrestricted:</b>\n\n⚡ Talk to me:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("🐬 <b>Dolphin is generating...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_dolphin(client, prompt)
    await msg.edit_text(f"🐬 <b>Dolphin Unrestricted:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_mistral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_MISTRAL] = True
        await update.effective_message.reply_text("🌪 <b>Mistral 3.1:</b>\n\n⚡ Enter prompt:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("🌪 <b>Mistral is generating...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_mistral(client, prompt)
    await msg.edit_text(f"🌪 <b>Mistral 3.1:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_zerotwo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_ZEROTWO] = True
        await update.effective_message.reply_text("💕 <b>Zero Two:</b>\n\nHey darling... tell me what's on your mind~", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("💕 <b>Zero Two is typing...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_zerotwo(client, prompt)
    await msg.edit_text(f"💕 <b>Zero Two:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_granite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_GRANITE] = True
        await update.effective_message.reply_text("💎 <b>Granite 4.0:</b>\n\n⚡ Talk to me:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("💎 <b>Granite 4.0 is thinking...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_granite(client, prompt)
    await msg.edit_text(f"💎 <b>Granite 4.0:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_llama4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_LLAMA4] = True
        await update.effective_message.reply_text("🦙 <b>Llama 4:</b>\n\n⚡ Talk to me:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("🦙 <b>Llama 4 is analyzing...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_llama4(client, prompt)
    await msg.edit_text(f"🦙 <b>Llama 4:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_copilot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    prompt = " ".join(context.args) if context.args else None
    if not prompt:
        context.user_data[AWAIT_COPILOT] = True
        await update.effective_message.reply_text("💡 <b>Copilot Thinking...</b>\n\nEnter your deep query:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.effective_message.reply_text("💡 <b>Processing deep intelligence...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_copilot(client, prompt)
    await msg.edit_text(reply, parse_mode="HTML")
async def cmd_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.effective_message.reply_text(" Usage: /gemini <prompt>")
        return
    prompt = " ".join(context.args)
    msg = await update.effective_message.reply_text(" Gemini 3 is thinking... ✨")
    async with httpx.AsyncClient() as client:
        reply = await fetch_gemini3(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f" <b>Gemini Response:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.effective_message.reply_text(" Usage: /deepseek <prompt>")
        return
    prompt = " ".join(context.args)
    msg = await update.effective_message.reply_text(" DeepSeek is searching... ✨")
    async with httpx.AsyncClient() as client:
        reply = await fetch_deepseek(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f" <b>DeepSeek Response:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_flirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.effective_message.reply_text(" Usage: /flirt <text>")
        return
    prompt = " ".join(context.args)
    msg = await update.effective_message.reply_text(" Thinking... ")
    async with httpx.AsyncClient() as client:
        reply = await fetch_flirt(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"💖 <b>Flirt AI:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_ai_combined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args: return
    prompt = " ".join(context.args)
    msg = await update.effective_message.reply_text(" Consultation in progress... ✨")
    async with httpx.AsyncClient() as client:
        t1 = fetch_chatgpt(client, prompt)
        t2 = fetch_gemini3(client, prompt)
        r1, r2 = await asyncio.gather(t1, t2)
    safe_r1, safe_r2 = html.escape(r1), html.escape(r2)
    await msg.edit_text(f" <b>Combined AI Results:</b>\n\n<b>ChatGPT:</b>\n{safe_r1}\n\n<b>Gemini:</b>\n{safe_r2}", parse_mode="HTML")

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.effective_message.reply_text("💡 <b>Usage:</b> <code>/code <describe your task></code>", parse_mode="HTML")
        return
    prompt = " ".join(context.args)
    status = await update.effective_message.reply_text("👨‍💻 <b>Senior Architect is architecting...</b>", parse_mode="HTML")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    async with httpx.AsyncClient() as client:
        reply = await fetch_code(client, prompt)
    
    # Advanced Code Wrapping
    if "```" not in reply:
        formatted_reply = f"<code>{html.escape(reply)}</code>"
    else:
        # Regex to highlight code blocks for Telegram's click-to-copy
        formatted_reply = re.sub(r'```(?:\w+)?\n(.*?)\n```', r'<pre><code>\1</code></pre>', reply, flags=re.DOTALL)
        # Escape remaining text but keep the pre/code tags
        # This is tricky with regex, so we do it simply:
        if "<pre><code>" not in formatted_reply:
             formatted_reply = f"<pre><code>{html.escape(reply)}</code></pre>"

    if len(reply) > 4000:
        file_path = f"code_{int(time.time())}.py"
        with open(file_path, "w", encoding="utf-8") as f: f.write(reply.replace("```python", "").replace("```", "").strip())
        await update.effective_message.reply_document(document=open(file_path, "rb"), caption="👨‍💻 <b>Code Solution Engineered.</b>", parse_mode="HTML")
        await status.delete()
        os.remove(file_path)
    else:
        await status.edit_text(f"👨‍💻 <b>Elite Code Synthesis:</b>\n\n{formatted_reply}", parse_mode="HTML")

async def cmd_webzip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.effective_message.reply_text("💡 <b>Usage:</b> <code>/webzip <url></code>", parse_mode="HTML")
        return
    url_target = context.args[0]
    msg = await update.effective_message.reply_text("📦 <b>Zipping website... this might take a moment.</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as c:
        try:
            url = SAVE_WEB_ZIP_API.format(url=quote(url_target))
            resp = await c.get(url, timeout=60.0)
            if resp.status_code == 200:
                data = resp.json()
                dl_url = data.get("result") or data.get("url") or data.get("download_url") if isinstance(data, dict) else None
                if dl_url:
                    await msg.edit_text(f"📦 <b>Web to Zip Successful!</b>\n\n📥 You can download your zipped website here: {dl_url}", parse_mode="HTML")
                else:
                    await msg.edit_text("❌ Failed to parse zip link from the API.", parse_mode="HTML")
            else:
                await msg.edit_text(f"❌ <b>Error:</b> API returned {resp.status_code}", parse_mode="HTML")
        except Exception as e:
            await msg.edit_text(f"❌ <b>Error:</b> {e}", parse_mode="HTML")

async def cmd_qrgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        help_text = (
            "🖼️ <b>Advanced QR Generator</b>\n\n"
            "<b>Usage:</b> <code>/qrgen [text] [options]</code>\n\n"
            "<b>Options:</b>\n"
            "+ <code>-c \"caption\"</code> (text below)\n"
            "+ <code>-d hex</code> (dark color, e.g. #ff0000)\n"
            "+ <code>-l hex</code> (light color)\n"
            "+ <code>-img url</code> (center image)\n"
            "+ <code>-m margin</code> (e.g. 4)\n"
            "+ <code>-ec L|M|Q|H</code> (error correction)\n"
            "+ <code>-s size</code> (e.g. 500)\n\n"
            "<b>Example:</b>\n"
            "<code>/qrgen https://google.com -c \"Google\" -d #4285F4 -m 10</code>"
        )
        await update.effective_message.reply_text(help_text, parse_mode="HTML")
        return

    raw_args = " ".join(context.args)
    # Improved parsing for flags
    text = raw_args
    params = {}
    
    if " -" in raw_args:
        # Split text from flags
        text_match = re.split(r'\s+-\w+', raw_args, maxsplit=1)
        text = text_match[0].strip()
        flags_part = raw_args[len(text):].strip()
        
        # Parse flags
        matches = re.findall(r'-(\w+)\s+(?:\"([^\"]+)\"|(\S+))', flags_part)
        for key, val1, val2 in matches:
            val = val1 or val2
            if key == "c": params["caption"] = val
            elif key == "d": params["dark"] = val.replace("#", "")
            elif key == "l": params["light"] = val.replace("#", "")
            elif key == "img": params["centerImageUrl"] = val
            elif key == "s": params["size"] = val
            elif key == "m": params["margin"] = val
            elif key == "ec": params["ecLevel"] = val.upper()

    msg = await update.effective_message.reply_text("✨ <b>Crafting Advanced QR...</b>", parse_mode="HTML")
    
    try:
        api_url = f"https://quickchart.io/qr?text={quote(text)}"
        for k, v in params.items():
            api_url += f"&{k}={quote(str(v))}"
        
        # Add high error correction if image is present
        if "centerImageUrl" in params:
            api_url += "&ecLevel=H"
            
        file_name = f"qr_{int(time.time())}.png"
        file_path = os.path.join("downloads", file_name)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=20.0)
            if resp.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(resp.content)
            else:
                await msg.edit_text(f"❌ <b>API Error:</b> <code>HTTP {resp.status_code}</code>", parse_mode="HTML")
                return

        await msg.delete()
        with open(file_path, "rb") as photo:
            await update.effective_message.reply_photo(
                photo=photo, 
                caption=f"✅ <b>QR Code Generated</b>\n\n <b>Content:</b> <code>{html.escape(text[:200])}</code>", 
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"QR Gen Error: {e}")
        await msg.edit_text(f"❌ <b>Generation Failed:</b> <code>System Error</code>", parse_mode="HTML")

async def cmd_qrread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = update.message
    photo = None
    
    if msg.reply_to_message and msg.reply_to_message.photo:
        photo = msg.reply_to_message.photo[-1]
    elif msg.photo:
        photo = msg.photo[-1]
    else:
        await msg.reply_text(" <b>Usage:</b> Reply to a photo with <code>/qrread</code> to scan it.", parse_mode="HTML")
        return

    status = await msg.reply_text(" <b>Processing Image for QR...</b>", parse_mode="HTML")
    try:
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Use multiple APIs as fallback for better detection
        async with httpx.AsyncClient() as client:
            # Plan A: qrserver api with multipart upload (more reliable)
            files = {'file': ('qr.jpg', bytes(file_bytes), 'image/jpeg')}
            resp = await client.post("https://api.qrserver.com/v1/read-qr-code/", files=files, timeout=20.0)
            data = resp.json()
            
        if data and isinstance(data, list) and data[0]['symbol'] and data[0]['symbol'][0]['data']:
            result = data[0]['symbol'][0]['data']
            await status.edit_text(f"✅ <b>QR Code Decoded:</b>\n\n<code>{html.escape(result)}</code>", parse_mode="HTML")
        else:
            await status.edit_text("❌ <b>Decode Failed:</b> No valid QR code detected in this image.")
    except Exception as e:
        logger.error(f"QR Read Error: {e}")
        await status.edit_text(f"❌ <b>System Error:</b> <code>Something went wrong while scanning.</code>", parse_mode="HTML")

async def cmd_webss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        await update.effective_message.reply_text("💡 <b>Usage:</b> <code>/webss <url></code>", parse_mode="HTML")
        return
    url = context.args[0]
    if not url.startswith("http"):
        url = "http://" + url
        
    msg = await update.effective_message.reply_text("📸 <b>Taking screenshot...</b>", parse_mode="HTML")
    api_url = WEBSS_API.format(url=quote(url))
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(api_url, timeout=40.0)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "image" in content_type:
                    success = await download_and_send_photo(client, api_url, update, f"📸 <b>WebSS:</b> {url}")
                    if success:
                        await msg.delete()
                        return
                    else:
                        await msg.edit_text("❌ Failed to send screenshot.")
                else:
                    data = resp.json()
                    img_url = data.get("result") or data.get("url") or data.get("download_url") if isinstance(data, dict) else None
                    if img_url:
                        success = await download_and_send_photo(client, img_url, update, f"📸 <b>WebSS:</b> {url}")
                        if success:
                            await msg.delete()
                            return
                        else:
                            await msg.edit_text("❌ Failed to send screenshot.")
                    else:
                        await msg.edit_text("❌ API returned invalid data.", parse_mode="HTML")
            else:
                await msg.edit_text(f"❌ <b>Error:</b> API returned {resp.status_code}", parse_mode="HTML")
        except Exception as e:
            logger.error(f"WebSS Error: {e}")
            await msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")



async def cmd_game_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    kb = [
        [InlineKeyboardButton("✊ Rock", callback_data="rps_rock"),
         InlineKeyboardButton("✋ Paper", callback_data="rps_paper"),
         InlineKeyboardButton("✌️ Scissors", callback_data="rps_scissors")],
        [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
    ]
    text = "✊ <b>Rock Paper Scissors</b> ✌️\n\nChallenge Hintata! Select your move:"
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def callback_rps_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_choice = query.data.split("_")[1]
    options = ["rock", "paper", "scissors"]
    bot_choice = random.choice(options)
    
    emoji_map = {"rock": "✊ Rock", "paper": "✋ Paper", "scissors": "✌️ Scissors"}
    
    result = ""
    if user_choice == bot_choice:
        result = "🎲 <b>It's a Tie!</b>"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = "🏆 <b>You Won!</b>"
    else:
        result = "💀 <b>Hinata Won!</b>"
        
    text = (
        f"✊ <b>RPS Battle Summary</b> ✌️\n"
        f"──────────────────\n"
        f"👤 <b>You:</b> {emoji_map[user_choice]}\n"
        f"🤖 <b>Hinata:</b> {emoji_map[bot_choice]}\n\n"
        f"👉 {result}"
    )
    kb = [[InlineKeyboardButton("🔄 Replay", callback_data="btn_rps"),
           InlineKeyboardButton("🔙 Exit", callback_data="btn_back")]]
    await safe_edit(query, text, reply_markup=InlineKeyboardMarkup(kb))

async def cmd_truthordare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    
    # Simplified Categories
    kb = [
        [InlineKeyboardButton("😂 Truth", callback_data="tod_truth"),
         InlineKeyboardButton("🤪 Dare", callback_data="tod_dare")],
        [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
    ]
    text = "🎲 <b>Truth or Dare?</b>\n\n👇 Select one below:"
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")



# ================= Flows & State Management =================
AWAIT_GEMINI = "await_gemini"
AWAIT_DEEPSEEK = "await_deepseek"
AWAIT_FLIRT = "await_flirt"
AWAIT_INSTA = "await_insta"
AWAIT_USERINFO = "await_userinfo"
AWAIT_FF = "await_ff"
AWAIT_FFGUILD = "await_ffguild"
AWAIT_CODE = "await_code"
AWAIT_DL = "await_dl"
AWAIT_QRGEN = "await_qrgen"
AWAIT_BGREM = "await_bgrem"
AWAIT_TRANSLATE = "await_translate"
AWAIT_SUMMARIZE = "await_summarize"
AWAIT_GRAMMAR = "await_grammar"
AWAIT_BAN = "await_ban"
AWAIT_UNBAN = "await_unban"
AWAIT_GUESS = "await_guess"
AWAIT_RIDDLE = "await_riddle"
AWAIT_HINATA = "await_hinata"
AWAIT_IMAGINE = "await_imagine"
AWAIT_TRIVIA = "await_trivia"
AWAIT_DETECTOR = "await_detector"
AWAIT_WEBSS = "await_webss"
AWAIT_EMAIL = "await_email"
AWAIT_PINTEREST = "await_pinterest"
AWAIT_SHORTEN = "await_shorten"
AWAIT_TTSTALK = "await_ttstalk"
AWAIT_YTSEARCH = "await_ytsearch"
AWAIT_COPILOT = "await_copilot"
AWAIT_STYLETEXT = "await_styletext"
AWAIT_CHATGPT = "await_chatgpt"
AWAIT_LYRICS = "await_lyrics"
AWAIT_WRITE = "await_write"
AWAIT_ASK = "await_ask"
AWAIT_BIO = "await_bio"
AWAIT_POEM = "await_poem"
AWAIT_STORY = "await_story"
AWAIT_ADVICE = "await_advice"
AWAIT_ROAST = "await_roast"
AWAIT_JOKE = "await_joke"
AWAIT_DOLPHIN = "await_dolphin"
AWAIT_GRANITE = "await_granite"
AWAIT_LLAMA4 = "await_llama4"
AWAIT_WEBZIP = "await_webzip"
AWAIT_KEEPER_ADD = "await_keeper_add"
AWAIT_KEEPER_DEL = "await_keeper_del"
AWAIT_ZEROTWO = "await_zerotwo"
AWAIT_MISTRAL = "await_mistral"

def clear_states(ud):
    """Clears all pending prompt states to prevent tool conflicts."""
    for key in [AWAIT_GEMINI, AWAIT_DEEPSEEK, AWAIT_CHATGPT, AWAIT_FLIRT, AWAIT_INSTA, AWAIT_USERINFO, 
AWAIT_FF, AWAIT_CODE, AWAIT_DL, AWAIT_QRGEN, AWAIT_BGREM, AWAIT_TRANSLATE, AWAIT_SUMMARIZE, AWAIT_GRAMMAR, AWAIT_BAN, 
AWAIT_UNBAN, AWAIT_GUESS, AWAIT_RIDDLE, AWAIT_HINATA, AWAIT_TRIVIA, AWAIT_PINTEREST, AWAIT_YTSEARCH, 
AWAIT_COPILOT, AWAIT_STYLETEXT, AWAIT_IMAGINE, AWAIT_TTSTALK, AWAIT_SHORTEN, AWAIT_EMAIL, AWAIT_DETECTOR, AWAIT_WEBSS,
AWAIT_POEM, AWAIT_STORY, AWAIT_ADVICE, AWAIT_ROAST, AWAIT_JOKE, AWAIT_DOLPHIN, AWAIT_GRANITE, AWAIT_LLAMA4, AWAIT_WEBZIP,
AWAIT_KEEPER_ADD, AWAIT_KEEPER_DEL, AWAIT_ZEROTWO, AWAIT_MISTRAL]:
        ud.pop(key, None)

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    msg = update.message if update.message else update.callback_query.message
    status = await msg.reply_text("🔍 <b>Analyzing URL...</b>\n<i>Connecting to neural engines...</i>", parse_mode="HTML")
    os.makedirs("downloads", exist_ok=True)
    
    # Platform branding detection
    platform_icon = "🔗"
    if "youtube.com" in url or "youtu.be" in url: platform_icon = "🎬"
    elif "instagram.com" in url: platform_icon = "📸"
    elif "tiktok.com" in url: platform_icon = "📱"
    elif "facebook.com" in url or "fb.watch" in url: platform_icon = "👥"
    elif "twitter.com" in url or "x.com" in url: platform_icon = "🐦"
    elif "mediafire.com" in url: platform_icon = "📂"
    elif "terabox.com" in url or "teraboxapp.com" in url: platform_icon = "📦"
    elif "snapchat.com" in url: platform_icon = "👻"
    elif "spotify.com" in url: platform_icon = "🎵"
    elif "soundcloud.com" in url: platform_icon = "☁️"

    # Check for specific platform APIs first
    api_url = None
    if "mediafire.com" in url:
        api_url = MEDIAFIRE_DL_API.format(url=quote(url))
    elif "terabox.com" in url or "teraboxapp.com" in url:
        api_url = TERABOX_DL_API.format(url=quote(url))
    elif "youtube.com" in url or "youtu.be" in url:
        api_url = YOUTUBE_DL_API.format(url=quote(url))
    elif "pin.it" in url or "pinterest.com" in url:
        api_url = PINTEREST_DL_API.format(url=quote(url))
    elif "instagram.com" in url:
        api_url = INSTA_DL_API.format(url=quote(url))
    elif "tiktok.com" in url:
        api_url = TIKTOK_DL_API.format(url=quote(url))
    else:
        # Generic AIO Fallback
        api_url = AIO_DL_API.format(url=quote(url))

    if api_url:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(api_url, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    dl_url, title = None, "Media Cloud File"
                    
                    # Extensive Deep Extraction Logic
                    def extract_deep(obj):
                        if not obj: return None
                        # Priority Keys
                        for k in ["download_url", "download", "url_hd", "url", "link", "video", "image", "direct_link"]:
                            if obj.get(k) and isinstance(obj[k], str) and (obj[k].startswith("http") or obj[k].startswith("/")):
                                return obj[k]
                        return None

                    # 1. Check result list
                    res = data.get("result") or data.get("data")
                    if isinstance(res, list) and len(res) > 0:
                        dl_url = extract_deep(res[0])
                        title = res[0].get("title") or res[0].get("filename") or res[0].get("name", title)
                    # 2. Check result dict
                    elif isinstance(res, dict):
                        dl_url = extract_deep(res)
                        title = res.get("title") or res.get("filename") or res.get("name", title)
                    # 3. Check root
                    if not dl_url:
                        dl_url = extract_deep(data)
                        title = data.get("title") or data.get("name") or data.get("filename", title)
                    
                    # 4. Special cases (Mediafire/etc)
                    if not dl_url and "link" in data: dl_url = data["link"]
                    if not dl_url and "url" in data: dl_url = data["url"]

                    # Specifically check for YTDL formats array
                    if not dl_url and isinstance(data, dict) and "formats" in data and isinstance(data["formats"], list):
                        vids = [f for f in data["formats"] if f.get("type", "") == "video"]
                        auds = [f for f in data["formats"] if f.get("type", "") == "audio"]
                        
                        target_format = context.user_data.pop("ytdl_type_override", None)
                        sources = auds if target_format == "aud" else vids
                        if not sources: sources = data["formats"]
                        
                        if sources:
                            dl_url = sources[-1].get("url")
                            title = data.get("info", {}).get("title", title)

                    if dl_url:
                        await status.edit_text(f"{platform_icon} <b>Link Decoded!</b>\n<i>Initiating binary stream...</i>", parse_mode="HTML")
                        try:
                            # Improved Extension Detection
                            file_ext = "mp4" # Default for most media sites
                            try:
                                # Quick head request to check content type
                                async with client.stream("GET", dl_url, timeout=10.0) as st:
                                    ct = st.headers.get("Content-Type", "").lower()
                                    if "video" in ct: file_ext = "mp4"
                                    elif "audio" in ct: file_ext = "mp3"
                                    elif "image" in ct: file_ext = "jpg"
                                    else:
                                        # Fallback to URL parsing
                                        ext_part = dl_url.split("?")[0].split(".")[-1].lower()
                                        if len(ext_part) <= 4 and ext_part.isalnum():
                                            file_ext = ext_part
                                        else:
                                            # Platform specific defaults
                                            if any(x in url.lower() for x in ["youtube", "youtu.be", "tiktok", "instagram", "facebook"]):
                                                file_ext = "mp4"
                                            else:
                                                file_ext = "bin"
                            except:
                                # On timeout or error, use platform detection
                                if any(x in url.lower() for x in ["youtube", "youtu.be", "tiktok", "instagram", "facebook"]):
                                    file_ext = "mp4"
                                else:
                                    file_ext = "bin"
                            
                            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
                            if not safe_title: safe_title = "download"
                            local_path = os.path.join("downloads", f"{safe_title}_{int(time.time())}.{file_ext}")
                            
                            # Download using httpx
                            async with getattr(client, "stream", client.stream)("GET", dl_url, timeout=120.0) as st_resp:
                                if st_resp.status_code == 200:
                                    with open(local_path, "wb") as f:
                                        async for chunk in st_resp.aiter_bytes(chunk_size=8192):
                                            f.write(chunk)
                                            
                            # Use video for video sites, else document
                            is_video = file_ext in ["mp4", "mkv", "mov", "webm"] or any(x in url.lower() for x in ["youtube", "youtu.be", "tiktok", "instagram", "facebook", "fb.watch", "twitter", "x.com"])
                            
                            with open(local_path, "rb") as f:
                                try:
                                    if is_video:
                                        await context.bot.send_video(
                                            chat_id=update.effective_chat.id,
                                            video=f,
                                            caption=f"📥 <b>{html.escape(title[:60])}</b>\n\n🚀 <i>Successfully synced via Premium Hub</i> ✨",
                                            parse_mode="HTML"
                                        )
                                    else:
                                        await context.bot.send_document(
                                            chat_id=update.effective_chat.id, 
                                            document=f, 
                                            caption=f"📥 <b>{html.escape(title[:60])}</b>\n\n🚀 <i>Successfully synced via Premium Hub</i> ✨", 
                                            parse_mode="HTML"
                                        )
                                except:
                                    f.seek(0)
                                    await context.bot.send_document(
                                        chat_id=update.effective_chat.id, 
                                        document=f, 
                                        caption=f"📥 <b>{html.escape(title[:60])}</b>\n\n🚀 <i>Emergency Document Fallback</i> ✨", 
                                        parse_mode="HTML"
                                    )
                            
                            await status.delete()
                            try: os.remove(local_path)
                            except: pass
                            return
                        except Exception as e:
                            logger.error(f"Direct Send Failed: {e}")
        except Exception as e:
            logger.error(f"Platform API Failure: {e}")

    # Fallback to local yt-dlp engine
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'format': 'best'
    }
    
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        await status.edit_text(f"{platform_icon} <b>Neural Extraction...</b>\n<i>Parsing manifest files...</i>", parse_mode="HTML")
        loop = asyncio.get_running_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
        title = info.get('title', 'Media Output')
        uploader = info.get('uploader', 'Unknown Source')
        duration = str(timedelta(seconds=info.get('duration', 0))) if info.get('duration') else "Live/Unknown"
        views = info.get('view_count', 0)
        
        context.user_data['dl_info'] = {
            'url': url,
            'title': title,
            'uploader': uploader,
            'duration': duration,
            'views': f"{views:,}" if views else "N/A"
        }
        
        kb = [
            [InlineKeyboardButton("🎬 Video Best", callback_data="dl_fmt|b|mp4"),
             InlineKeyboardButton("🎵 Audio MP3", callback_data="dl_fmt|ba/b|mp3")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back")]
        ]
        
        ui_text = (
            f"📡 <b>Matrix Capture Successful</b> {platform_icon}\n\n"
            f"🏷 <b>Title:</b> <code>{html.escape(title[:80])}</code>\n"
            f"👤 <b>By:</b> <code>{html.escape(uploader)}</code>\n"
            f"🕒 <b>Length:</b> <code>{duration}</code>\n\n"
            f"<i>Select your preferred output format:</i>"
        )
        await status.edit_text(ui_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Extraction Error: {e}")
        err = str(e)
        if "Sign in" in err:
             await status.edit_text("🔒 <b>Access Restricted.</b>\n<i>Sign-in required for this content (Age/Geo block).</i>", parse_mode="HTML")
        elif "DRM" in err:
             await status.edit_text("🔒 <b>DRM Protected Content.</b>\n<i>This video uses Digital Rights Management and cannot be downloaded due to copyright protections.</i>", parse_mode="HTML")
        elif "Requested format is not available" in err:
             await status.edit_text("⚠️ <b>Format Error.</b>\n<i>The requested quality or format is not available for this specific video.</i>", parse_mode="HTML")
        else:
             await status.edit_text(f"❌ <b>Extraction Failure:</b>\n<code>{html.escape(err[:100])}</code>\n\n<i>Try another link!</i>", parse_mode="HTML")


    
async def progress_hook(d, status_msg, state):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '0%').replace('%','').strip()
            try: per = float(p)
            except: per = 0
            
            if per < state.get('last_per', 0) - 20: 
                state['part'] = state.get('part', 1) + 1
            state['last_per'] = per

            bar_len = 12
            filled = int(per / 100 * bar_len)
            bar = "▓" * filled + "░" * (bar_len - filled)
            
            speed = d.get('_speed_str', 'N/A')
            size = d.get('_total_bytes_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            text = (
                f"🛰 <b>Neural Stream Connection Established</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📥 <b>Status:</b> <code>Downloading Part {state.get('part', 1)}</code>\n\n"
                f"<code>{bar} {per:.1f}%</code>\n"
                f"🚀 <b>Velocity:</b> <code>{speed}</code>\n"
                f"💾 <b>Payload:</b> <code>{size}</code>\n"
                f"⏳ <b>ETA:</b> <code>{eta}</code>\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            
            if time.time() - state.get('last_update', 0) > 2.5 or per >= 100:
                 state['last_update'] = time.time()
                 await status_msg.edit_text(text, parse_mode="HTML")
        except: pass
    elif d['status'] == 'finished':
        try: await status_msg.edit_text("⚙️ <b>Assembling Packets...</b>\n<i>Finalizing binary integrity...</i>", parse_mode="HTML")
        except: pass

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE, format_id: str, extension: str):
    query = update.callback_query
    await query.answer()
    dl_info = context.user_data.get('dl_info')
    if not dl_info:
        await query.edit_message_text("❌ <b>Session Expired.</b>\nPlease try /dl again.")
        return

    url = dl_info['url']
    status_msg = await query.edit_message_text(f"🏁 <b>Processing Engine...</b>\n<i>Mode: {extension.upper()} | Syncing...</i>", parse_mode="HTML")
    
    filename = f"downloads/hinata_{int(time.time())}.{extension}"
    loop = asyncio.get_running_loop()
    dl_state = {'part': 1, 'last_per': 0, 'last_update': 0}

    def hook(d):
        try: asyncio.run_coroutine_threadsafe(progress_hook(d, status_msg, dl_state), loop)
        except: pass

    ydl_opts = {
        'format': format_id,
        'outtmpl': filename,
        'restrictfilenames': True,
        'quiet': True,
        'max_filesize': 450 * 1024 * 1024, # Increased to 450MB
    }
    
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    ydl_opts['progress_hooks'] = [hook]

    if extension == "mp3":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        await loop.run_in_executor(None, run_yt_dlp, ydl_opts, url)
            
        actual_file = filename
        if extension == "mp3":
            # Postprocessors often change name
            fbase = os.path.splitext(filename)[0]
            if os.path.exists(fbase + ".mp3"):
                actual_file = fbase + ".mp3"
            elif not os.path.exists(filename):
                # Fallback search
                for f in os.listdir("downloads"):
                    if f.startswith("hinata_") and f.endswith(".mp3"):
                        actual_file = os.path.join("downloads", f)
                        break

        if not os.path.exists(actual_file):
             await status_msg.edit_text("❌ <b>Packet Loss Detected.</b>\n<i>The file failed to save locally.</i>", parse_mode="HTML")
             return

        fsize = os.path.getsize(actual_file)
        if fsize > 1.9 * 1024 * 1024 * 1024: # 1.9GB Telegram limit
            os.remove(actual_file)
            await status_msg.edit_text("⚠️ <b>Exceeds Telegram Payload!</b>\n<i>File is over 2GB. Try lower quality.</i>", parse_mode="HTML")
            return

        await status_msg.edit_text("☁️ <b>Cloud Uploading...</b>\n<i>Syncing with Telegram servers...</i>", parse_mode="HTML")
        
        cap = (
            f"🎬 <b>{html.escape(dl_info['title'][:100])}</b>\n\n"
            f"👤 <b>Uploader:</b> <code>{html.escape(dl_info['uploader'])}</code>\n"
            f"🕒 <b>Duration:</b> <code>{dl_info['duration']}</code>\n"
            f"💾 <b>File Size:</b> <code>{fsize/(1024*1024):.1f} MB</code>\n"
            f"📡 <b>Status:</b> <code>Binary Sync Core V3</code>\n\n"
            f"✨ <i>Managed by {BOT_NAME} Neural Network</i>"
        )

        with open(actual_file, 'rb') as f:
            if extension == "mp3":
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=cap, parse_mode="HTML", read_timeout=120)
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=f, caption=cap, parse_mode="HTML", read_timeout=300, supports_streaming=True)

        await status_msg.delete()
        if os.path.exists(actual_file): os.remove(actual_file)

    except Exception as e:
        logger.error(f"DL Process Error: {e}")
        await status_msg.edit_text(f"❌ <b>Neural Link Broken:</b>\n<code>{html.escape(str(e))[:120]}</code>", parse_mode="HTML")

def run_yt_dlp(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

async def do_insta_fetch_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    msg = await update.effective_message.reply_text(" <b>Searching Instagram Profile...</b>", parse_mode="HTML")
    # Clean username
    username = username.replace("@", "").strip().split("/")[-1]
    
    # Try multiple free endpoints as fallbacks
    urls = [
        f"https://apis.prexzyvilla.site/stalk/ig?user={username}",
        f"https://apis.prexzyvilla.site/stalk/igstalk?username={username}",
        f"https://instagram-api-ashy.vercel.app/api/ig-profile.php?username={username}",
        f"https://insta-profile-api.onrender.com/api/profile/{username}"
    ]
    
    data = None
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                data = await fetch_json(client, url)
                if data:
                    res = data.get("profile") or data.get("data") or data.get("result")
                    status_ok = data.get("status") in [True, "ok", 200]
                    if res or status_ok:
                        break
            except: continue

    p = None
    if data:
        p = data.get("profile") or data.get("data") or data.get("result")
    
    if not p:
        await msg.edit_text("❌ <b>Profile not found or API down.</b>\n<i>Please ensure the username is correct and public, or try again later.</i>", parse_mode="HTML")
        return
    
    # Robust extraction with count formatting
    def f_cnt(v):
        try:
            if isinstance(v, str): v = v.replace(",", "")
            return f"{int(v):,}"
        except: return str(v or 0)

    full_name = html.escape(str(p.get('full_name') or p.get('full_name_hd') or "Unknown"))
    uname = html.escape(str(p.get('username') or username))
    bio = html.escape(str(p.get('biography') or p.get('bio') or "No biography set"))
    followers = f_cnt(p.get('followers') or p.get('follower_count'))
    following = f_cnt(p.get('following') or p.get('following_count'))
    posts = f_cnt(p.get('posts') or p.get('media_count'))
    user_id = p.get('id') or p.get('pk') or 'N/A'
    
    is_private = "Yes 🔒" if p.get('is_private') else "No 🔓"
    is_verified = "Yes ✅" if p.get('is_verified') else "No ❌"
    is_business = "Yes 🏢" if p.get('is_business_account') or p.get('is_business') else "No 👤"
    created_year = p.get('account_creation_year') or "Secret 🕵️"

    cap = (
        f"🌌 <b>INSTAGRAM NEURAL DOSSIER</b> 🌌\n"
        f"────────────────────\n"
        f"👤 <b>Name:</b> <code>{full_name}</code>\n"
        f"📸 <b>Handle:</b> @{uname}\n"
        f"🆔 <b>Entity ID:</b> <code>{user_id}</code>\n\n"
        f"📊 <b>Network Stats:</b>\n"
        f"├ 👥 <b>Followers:</b> <code>{followers}</code>\n"
        f"├ 📡 <b>Following:</b> <code>{following}</code>\n"
        f"└ 📤 <b>Transmissions:</b> <code>{posts}</code>\n\n"
        f"🛡 <b>Verification:</b>\n"
        f"├ 🔒 <b>Private:</b> <code>{is_private}</code>\n"
        f"├ ✅ <b>Verified:</b> <code>{is_verified}</code>\n"
        f"└ 🏢 <b>Business:</b> <code>{is_business}</code>\n\n"
        f"📜 <b>Bio-Signature:</b>\n<i>{bio}</i>"
    )

    
    pic = p.get("profile_pic_url_hd") or p.get("hd_profile_pic_url_info", {}).get("url") or p.get("profile_pic_url")
    if pic:
        try:
            await msg.delete()
            await update.effective_message.reply_photo(photo=pic, caption=cap[:1024], parse_mode="HTML")
        except:
            await update.effective_message.reply_text(cap, parse_mode="HTML")
    else:
        await msg.edit_text(cap, parse_mode="HTML")


async def do_ff_fetch_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str):
    msg = await update.effective_message.reply_text("🎮 <b>Accessing Garena Databases...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(FF_API.format(uid), timeout=40.0)
            if resp.status_code == 200:
                data = resp.json()
                bi = data.get("basicInfo", {})
                ci = data.get("clanBasicInfo", {})
                si = data.get("socialInfo", {})
                credit = data.get("creditScoreInfo", {})
                
                if bi:
                    name = html.escape(str(bi.get("nickname") or "Unknown"))
                    level = bi.get("level", "N/A")
                    exp = bi.get("exp", "N/A")
                    region = bi.get("region", "Global")
                    likes = bi.get("liked", "0")
                    rank_points = bi.get("rankingPoints", "0")
                    
                    # Clan info
                    clan = html.escape(str(ci.get("clanName") or "No Clan"))
                    clan_lv = ci.get("clanLevel", "0")
                    
                    # Social info
                    bio = html.escape(str(si.get("signature") or "No signature set"))
                    # Filter out color codes if present (e.g. [FF0000])
                    bio = re.sub(r'\[[A-Z0-9]{6}\]', '', bio).replace('[b]', '').replace('[i]', '').replace('[/b]', '').replace('[/i]', '')
                    
                    gender = si.get("gender", "N/A").replace("Gender_", "")
                    lang = si.get("language", "N/A").replace("Language_", "")
                    
                    text = (
                        f"🎮 <b>FREE FIRE AGENT SCAN v2.0</b> 🎮\n"
                        f"────────────────────\n"
                        f"👤 <b>Agent:</b> <code>{name}</code>\n"
                        f"🆔 <b>UID:</b> <code>{uid}</code>\n"
                        f"🏅 <b>Level:</b> <code>{level}</code>\n"
                        f"📈 <b>Exp:</b> <code>{exp:,}</code>\n"
                        f"🌍 <b>Sector:</b> <code>{region}</code>\n"
                        f"❤️ <b>Likes:</b> <code>{likes:,}</code>\n"
                        f"🏆 <b>Rank Points:</b> <code>{rank_points:,}</code>\n"
                        f"────────────────────\n"
                        f"🛡 <b>Clan:</b> <code>{clan}</code> (Lv.{clan_lv})\n"
                        f"👫 <b>Gender:</b> <code>{gender}</code>\n"
                        f"🌐 <b>Language:</b> <code>{lang}</code>\n"
                        f"💯 <b>Credit Score:</b> <code>{credit.get('creditScore', '100')}</code>\n"
                        f"────────────────────\n"
                        f"📜 <b>Signature:</b>\n<i>{bio}</i>"
                    )
                    await msg.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
                    return
            await msg.edit_text("❌ <b>Access Denied:</b> UID not found in Garena registry.")
        except Exception as e:
            logger.exception("FF Stalk Error")
            await msg.edit_text(f"❌ <b>Neural Error:</b> {html.escape(str(e))}")

async def do_user_info_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    target_user = None
    chat_obj = None
    
    if update.message and update.effective_message.reply_to_message:
        target_user = update.effective_message.reply_to_message.from_user
    elif query:
        try:
            if query.startswith("@"): query = query[1:]
            if query.isdigit():
                try:
                    chat_obj = await context.bot.get_chat(int(query))
                    target_user = chat_obj
                except: 
                    await update.effective_message.reply_text("❌ <b>User not found by ID.</b>", parse_mode="HTML")
                    return
            else:
                try:
                    chat_obj = await context.bot.get_chat(f"@{query}")
                    target_user = chat_obj
                except:
                    await update.effective_message.reply_text(f"❌ <b>User @{query} not found.</b>", parse_mode="HTML")
                    return
        except Exception as e:
            logger.error(f"User Info Error: {e}")
            await update.effective_message.reply_text("❌ <b>Error fetching user.</b>", parse_mode="HTML")
            return
    else:
        target_user = update.effective_user

    if not target_user: return

    status_msg = await update.effective_message.reply_text("🔍 <b>Scanning Telegram Cryptographic Database...</b>", parse_mode="HTML")
    
    # Attempt to get full chat object for Bio and other details
    try:
        if not chat_obj:
            chat_obj = await context.bot.get_chat(target_user.id)
    except: pass

    # Data extraction
    uid = target_user.id
    first_name = html.escape(target_user.first_name or "N/A")
    last_name = html.escape(target_user.last_name or "")
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{target_user.username}" if target_user.username else "None"
    bio = html.escape(chat_obj.bio or "No Bio") if chat_obj and hasattr(chat_obj, 'bio') else "N/A"
    dc_id = getattr(target_user, 'dc_id', "N/A")
    is_premium = "Yes 💎" if getattr(target_user, 'is_premium', False) else "No"
    is_bot = "Yes 🤖" if getattr(target_user, 'is_bot', False) else "No"
    is_scam = "Yes ⚠️" if getattr(target_user, 'scam', False) else "No"
    is_fake = "Yes 🚫" if getattr(target_user, 'fake', False) else "No"
    is_restricted = "Yes 🔒" if getattr(target_user, 'is_restricted', False) else "No"
    
    # Link to user
    mention = f"<a href='tg://user?id={uid}'>{full_name}</a>"
    
    # Profile Pic Check
    pfp_count = 0
    try:
        photos = await context.bot.get_user_profile_photos(uid, limit=1)
        pfp_count = photos.total_count
    except: pass

    # Account Era based on ID
    era = "Ancient 🏛️" if uid < 100000000 else "Glory Days 🎖️"
    if 500000000 <= uid < 1000000000: era = "Pre-Global 🌍"
    if 1000000000 <= uid < 5000000000: era = "Global Era 🚀"
    if 5000000000 <= uid < 7000000000: era = "New Wave 🌊"
    if uid >= 7000000000: era = "The Future ✨"

    text = (
        f"👤 <b>TELEGRAM NEURAL PROFILE</b> 👤\n"
        f"────────────────────\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"👤 <b>Name:</b> {mention}\n"
        f"📝 <b>First Name:</b> <code>{first_name}</code>\n"
        f"📝 <b>Last Name:</b> <code>{last_name or 'N/A'}</code>\n"
        f"🌐 <b>Username:</b> {username}\n"
        f"🎯 <b>DC ID:</b> <code>{dc_id}</code>\n"
        f"📅 <b>Account Era:</b> <code>{era}</code>\n"
        f"────────────────────\n"
        f"💎 <b>Premium:</b> {is_premium}\n"
        f"🤖 <b>Bot:</b> {is_bot}\n"
        f"🖼 <b>Profile Pics:</b> {pfp_count}\n"
        f"────────────────────\n"
        f"⚖️ <b>Scam:</b> {is_scam}\n"
        f"🚫 <b>Fake:</b> {is_fake}\n"
        f"🔒 <b>Restricted:</b> {is_restricted}\n"
        f"────────────────────\n"
        f"📜 <b>Bio:</b>\n<i>{bio}</i>\n"
        f"────────────────────\n"
        f"🔗 <b>Permanent Link:</b>\n<a href='tg://user?id={uid}'>tg://user?id={uid}</a>"
    )

    try:
        # Try to send with profile pic if exists
        if pfp_count > 0:
            photo = photos.photos[0][-1].file_id
            await update.effective_chat.send_photo(photo=photo, caption=text, parse_mode="HTML")
            await status_msg.delete()
        else:
            await status_msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)
    except:
        await status_msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)

async def cmd_bgrem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = update.message
    if not msg.reply_to_message or not msg.reply_to_message.photo:
        await msg.reply_text(" <b>Usage:</b> Reply to a photo with <code>/bgrem</code> to remove its background.", parse_mode="HTML")
        return
    await do_bg_remove(update, context)

async def do_bg_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    target_msg = msg.reply_to_message if msg.reply_to_message else msg
    
    if not target_msg.photo:
        await msg.reply_text("❌ <b>Error:</b> No photo found to process.")
        return
        
    status = await msg.reply_text(" <b>Removing background...</b>", parse_mode="HTML")
    
    try:
        # Download photo
        file = await context.bot.get_file(target_msg.photo[-1].file_id)
        img_bytes = await file.download_as_bytearray()
        
        async with httpx.AsyncClient() as client:
            files = {'image_file': ('image.jpg', bytes(img_bytes), 'image/jpeg')}
            headers = {'X-Api-Key': BG_REMOVE_KEY}
            resp = await client.post(BG_REMOVE_API, files=files, headers=headers, data={'size': 'auto'}, timeout=30.0)
            
            if resp.status_code == 200:
                output = io.BytesIO(resp.content)
                output.name = "no_bg.png"
                await status.delete()
                await msg.reply_document(document=output, caption="✅ <b>Background Removed!</b>", parse_mode="HTML")
            else:
                err_data = resp.json()
                err_msg = err_data.get('errors', [{}])[0].get('title', 'API Error')
                await status.edit_text(f"❌ <b>Error:</b> {err_msg}")
    except Exception as e:
        logger.error(f"BG Removal Error: {e}")
        await status.edit_text("❌ <b>System Error:</b> Failed to process image.")

async def do_ff_visit(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str):
    msg = await update.effective_message.reply_text(f" <b>Visiting Account {uid}...</b>", parse_mode="HTML")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(FF_VISIT_API.format(uid), timeout=20.0)
            data = resp.json()
            
        # Example: {"Credits":"MAXIM CODEX 07","FailedVisits":153,"PlayerNickname":"...","SuccessfulVisits":851,"TotalVisits":1004,"UID":...}
        if "TotalVisits" in data:
            nick = html.escape(data.get("PlayerNickname", "Unknown"))
            total = data.get("TotalVisits", 0)
            success = data.get("SuccessfulVisits", 0)
            failed = data.get("FailedVisits", 0)
            credits = html.escape(data.get("Credits", "Unknown"))
            
            text = (
                f" <b>Account Visited Successfully</b>\n\n"
                f" <b>Player:</b> {nick}\n"
                f" <b>UID:</b> <code>{uid}</code>\n\n"
                f" <b>Visit Stats:</b>\n"
                f"✨ <b>Successful:</b> {success}\n"
                f"❌ <b>Failed:</b> {failed}\n"
                f" <b>Total:</b> {total}\n"
            )
            await msg.edit_text(text, parse_mode="HTML")
        else:
             await msg.edit_text(f"❌ <b>Error:</b> Unexpected API response.\n<code>{html.escape(str(data))}</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"FF Visit Error: {e}")
        await msg.edit_text("❌ <b>System Error:</b> Visit service timed out.")

async def cmd_ff_visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        await update.effective_message.reply_text(" <b>Usage:</b> <code>/visit [uid]</code>", parse_mode="HTML")
        return
    await do_ff_visit(update, context, context.args[0])

async def cmd_hinata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.effective_message.reply_text(" <b>Usage:</b> <code>/hinata [message]</code>\n\n<i>Talk to me...</i>", parse_mode="HTML")
        return
    prompt = " ".join(context.args)
    msg = await update.effective_message.reply_text(" <b>Hinata is typing...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_hinata(client, prompt)
    await msg.edit_text(f" <b>Hinata:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_detector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        await update.effective_message.reply_text("🔍 <b>Usage:</b> <code>/detector [text]</code>", parse_mode="HTML")
        return
    
    msg = await update.effective_message.reply_text("🛡 <b>Analyzing for AI patterns...</b>", parse_mode="HTML")
    try:
        url = AI_DETECTOR_API.format(text=quote(text))
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status"):
                    analysis = data.get("analysis", {})
                    ai_perc = analysis.get("ai_percentage", 0)
                    label = analysis.get("classification", "Unknown")
                    await msg.edit_text(
                        f"🛡 <b>AI Detection Report</b>\n\n"
                        f"🤖 <b>AI Percentage:</b> <code>{ai_perc}%</code>\n"
                        f"📊 <b>Classification:</b> <b>{label}</b>",
                        parse_mode="HTML"
                    )
                    return
                await msg.edit_text(f"❌ <b>Error:</b> {data.get('message', 'Detection failed')}")
            else:
                await msg.edit_text(f"❌ <b>Service Error:</b> HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Detector Error: {e}")
        await msg.edit_text("❌ <b>System Error:</b> Could not analyze text.")



async def cmd_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    usage = "📧 <b>Anonymous Email:</b>\n\n⚡ Usage: <code>/email to|subject|message</code>\n\n<i>Note: Use '|' as a separator.</i>"
    if not context.args or "|" not in " ".join(context.args):
        clear_states(context.user_data)
        context.user_data[AWAIT_EMAIL] = True
        if update.callback_query:
            await safe_edit(update.callback_query, usage, reply_markup=back_btn_kb())
        else:
            await update.effective_message.reply_text(usage, parse_mode="HTML", reply_markup=back_btn_kb())
        return
    
    try:
        parts = " ".join(context.args).split("|")
        if len(parts) < 3:
            await update.effective_message.reply_text(usage, parse_mode="HTML")
            return
        
        to_email, subject, body = parts[0].strip(), parts[1].strip(), parts[2].strip()
        msg = await update.effective_message.reply_text("📧 <b>Sending anonymous email...</b>", parse_mode="HTML")
        
        api_url = EMAIL_API.format(to=quote(to_email), subject=quote(subject), message=quote(body))
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") or data.get("success"):
                    await msg.edit_text("✅ <b>Email sent successfully!</b>", parse_mode="HTML")
                else:
                    await msg.edit_text(f"❌ <b>Failed:</b> {data.get('message', 'Service rejected')}")
            else:
                await msg.edit_text(f"❌ <b>Service Error:</b> HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Email Error: {e}")
        await update.effective_message.reply_text("❌ <b>System Error:</b> Could not send email.")
    
async def cmd_tempmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = await update.effective_message.reply_text(" <b>Creating Temporary Mailbox...</b>", parse_mode="HTML")
    
    async with httpx.AsyncClient() as client:
        tm = TempMailClient(client)
        if await tm.create_account():
            if await tm.login():
                 context.user_data['temp_mail'] = {
                     'email': tm.email,
                     'password': tm.password,
                     'token': tm.token
                 }
                 
                 kb = [[InlineKeyboardButton(" Refresh Inbox", callback_data="tm_refresh")],
                       [InlineKeyboardButton("✨ Close Session", callback_data="tm_close")]]
                 
                 text = (
                     f" <b>Temporary Mail Ready</b>\n\n"
                     f" <b>Email:</b> <code>{tm.email}</code>\n"
                     f" <b>Password:</b> <code>{tm.password}</code>\n\n"
                     f"<i>Waiting for emails... (Auto-refresh checks every user interaction or click Refresh)</i>"
                 )
                 await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            else:
                await msg.edit_text("✨ <b>Login Failed.</b>")
        else:
            await msg.edit_text("✨ <b>Account Creation Failed.</b>")

async def temp_mail_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE, manual=True):
    query = update.callback_query
    data = context.user_data.get('temp_mail')
    if not data:
        if manual: await query.answer("✨ Session Expired", show_alert=True)
        return

    async with httpx.AsyncClient() as client:
        tm = TempMailClient(client)
        tm.email = data['email']
        tm.token = data['token']
        
        try:
            msgs = await tm.get_messages()
            if not msgs:
                if manual: await query.answer(" Inbox Empty", show_alert=False)
                return
            
            # Show latest message
            latest = msgs[0]
            msg_id = latest['id']
            subject = latest.get('subject', 'No Subject')
            sender = latest.get('from', {}).get('address', 'Unknown')
            
            body = await tm.read_message(msg_id)
            
            # Extract OTP
            otp_match = re.search(r"\b\d{4,8}\b", body) or re.search(r"\b\d{4,8}\b", subject)
            otp = otp_match.group(0) if otp_match else "None"
            
            text = (
                 f" <b>New Email Received!</b>\n\n"
                 f" <b>To:</b> <code>{tm.email}</code>\n"
                 f" <b>From:</b> {sender}\n"
                 f" <b>Subject:</b> {subject}\n\n"
                 f" <b>Message:</b>\n{html.escape(body[:500])}...\n\n"
                 f" <b>OTP Detected:</b> <code>{otp}</code>"
            )
            
            kb = [[InlineKeyboardButton(" Refresh", callback_data="tm_refresh")],
                  [InlineKeyboardButton("✨ Close", callback_data="tm_close")]]
            
            await safe_edit(query, text, reply_markup=InlineKeyboardMarkup(kb))
            
        except Exception as e:
             if manual: await query.answer("✨ Error checking mail")


async def safe_edit(query, text, reply_markup=None, parse_mode="HTML"):
    try:
        if query.message.photo or query.message.video or query.message.animation:
            # If there's media, we must edit the caption instead of text
            await query.edit_message_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        err_str = str(e).lower()
        if "message is not modified" in err_str:
            return
        if "can't be edited" in err_str or "message to edit not found" in err_str:
             # Fallback: Delete and send new message
             try:
                 await query.message.delete()
             except: pass
             await query.bot.send_message(chat_id=query.message.chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
             logger.error(f"Safe Edit Failed: {e}")

# ================= Handlers =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    clear_states(context.user_data)
    
    # Try to answer query first to prevent loading icons
    try:
        await query.answer()
    except: pass
    
    # --- Handlers ---
    back = InlineKeyboardMarkup([[InlineKeyboardButton(" 🔙 Back", callback_data="btn_back")]])
    
    if data.startswith("menu_"):
        mtype = data.replace("menu_", "", 1)
        if mtype == "owner" and not is_owner(query.from_user.id):
             await query.answer(" 👑 Owner Only!", show_alert=True)
             return
        await query.edit_message_reply_markup(reply_markup=get_main_menu(mtype, query.from_user.id))
        return

    if data.startswith("rps_"):
        await callback_rps_handler(update, context)
        return

    # Check TTT Intercept first
    if data == "ttt_join" or data.startswith("ttt_move_"):
        await ttt_callback_handler(update, context)
        return

    if data.startswith("genimg_"):
        ratio = data.split("_")[1]
        await do_gem_image_gen(update, context, ratio)
        return
        
    if data.startswith("aiodl|"):
        idx = int(data.split("|")[1])
        await process_aio_download(update, context, idx)
        return

        
    elif data == "btn_poem":
        context.user_data[AWAIT_POEM] = True
        await safe_edit(query, "📜 <b>Poem Master:</b>\n\n⚡ Enter a theme or topic for the poem:", reply_markup=back)
    elif data == "btn_story":
        context.user_data[AWAIT_STORY] = True
        await safe_edit(query, "✍️ <b>Story AI:</b>\n\n⚡ Enter a prompt or title for the story:", reply_markup=back)
    elif data == "btn_advice":
        context.user_data[AWAIT_ADVICE] = True
        await safe_edit(query, "💡 <b>Life Advice:</b>\n\n⚡ Ask me anything you need guidance on:", reply_markup=back)
    elif data == "btn_roast":
        context.user_data[AWAIT_ROAST] = True
        await safe_edit(query, "🔥 <b>Brutal Roast:</b>\n\n⚡ Enter a name or topic to roast:", reply_markup=back)
    elif data == "btn_joke":
        context.user_data[AWAIT_JOKE] = True
        await safe_edit(query, "😂 <b>Random Joke:</b>\n\n⚡ Enter a topic or just say 'joke':", reply_markup=back)
    
    if data == "btn_gemini":
        context.user_data[AWAIT_GEMINI] = True
        await safe_edit(query, "🧠 <b>Gemini 3 Pro:</b>\n\n⚡ Enter your prompt below:", reply_markup=back)
    elif data == "btn_deepseek":
        context.user_data[AWAIT_DEEPSEEK] = True
        await safe_edit(query, "🔥 <b>DeepSeek v3:</b>\n\n⚡ Enter your prompt below:", reply_markup=back)
    elif data == "btn_flirt":
        context.user_data[AWAIT_FLIRT] = True
        await safe_edit(query, "💖 <b>Flirt AI:</b>\n\n😏 Enter text to flirt with:", reply_markup=back)
    elif data == "btn_code":
        context.user_data[AWAIT_CODE] = True
        await safe_edit(query, "👨‍💻 <b>Code Generator:</b>\n\n⌨️ Describe the code/task you need help with:", reply_markup=back)
    elif data == "btn_insta":
        context.user_data[AWAIT_INSTA] = True
        await safe_edit(query, "📸 <b>Instagram Info:</b>\n\n🔗 Enter Username or Profile URL:", reply_markup=back)
    elif data == "btn_userinfo":
        context.user_data[AWAIT_USERINFO] = True
        await safe_edit(query, "👤 <b>User Info:</b>\n\n🆔 Forward a message or enter User ID/Username:", reply_markup=back)
    elif data == "btn_ff":
        context.user_data[AWAIT_FF] = True
        await safe_edit(query, "🛡️ <b>Free Fire Stats:</b>\n\n🆔 Enter Player UID:", reply_markup=back)

    elif data == "btn_dl":
        context.user_data[AWAIT_DL] = True
        await safe_edit(query, "📥 <b>Multi-Downloader:</b>\n\n🔗 Enter any media URL (IG, TikTok, YT, Twitter, etc.):", reply_markup=back)
    elif data == "btn_qrgen":
        context.user_data[AWAIT_QRGEN] = True
        await safe_edit(query, "🔲 <b>QR Generator:</b>\n\n⌨️ Enter text or URL to generate QR:", reply_markup=back)
    elif data == "btn_translate":
        context.user_data[AWAIT_TRANSLATE] = True
        await safe_edit(query, "🌐 <b>AI Translator:</b>\n\n⌨️ Enter text to translate to English:", reply_markup=back)
    elif data == "btn_summarize":
        context.user_data[AWAIT_SUMMARIZE] = True
        await safe_edit(query, "📝 <b>AI Summarizer:</b>\n\n⌨️ Enter text to summarize:", reply_markup=back)
    elif data == "btn_grammar":
        context.user_data[AWAIT_GRAMMAR] = True
        await safe_edit(query, "🔡 <b>AI Grammar Check:</b>\n\n⌨️ Enter text to correct:", reply_markup=back)
    elif data == "btn_bgrem":
        context.user_data[AWAIT_BGREM] = True
        await safe_edit(query, "🖼️ <b>Background Remover:</b>\n\n📸 Send the photo you want to process:", reply_markup=back)
    elif data == "btn_detector":
        context.user_data[AWAIT_DETECTOR] = True
        await safe_edit(query, "🛡️ <b>AI Detector:</b>\n\n⌨️ Enter the text you want to analyze for AI patterns:", reply_markup=back)
    elif data == "btn_webss":
        context.user_data[AWAIT_WEBSS] = True
        await safe_edit(query, "📸 <b>Web Screenshot:</b>\n\n🔗 Enter the URL you want to capture:", reply_markup=back)
    elif data == "btn_email":
        await cmd_email(update, context)
    elif data == "btn_shorten":
        await cmd_shorten(update, context)
    elif data == "btn_pinterest":
        context.user_data[AWAIT_PINTEREST] = True
        await safe_edit(query, "📌 <b>Pinterest Discover:</b>\n\n⚡ Enter your search query below:", reply_markup=back)
    elif data == "btn_ytsearch":
        context.user_data[AWAIT_YTSEARCH] = True
        await safe_edit(query, "🎬 <b>YouTube Intelligence:</b>\n\n⚡ Enter video search query:", reply_markup=back)
    elif data == "btn_download_db_req":
        await cmd_download_db(update, context)
    elif data == "btn_ttt": await cmd_game_ttt(update, context)
    
    elif data == "btn_commands":
        await cmd_commands(update, context)
    elif data == "btn_help":
        await cmd_help(update, context)
    elif data == "btn_riddle":
        await cmd_game_riddle(update, context)
    elif data == "btn_guess":
        await cmd_game_guess(update, context)
    elif data == "btn_roast":
        await cmd_game_roast(update, context)
    elif data == "btn_joke":
        await cmd_game_joke(update, context)
        
    elif data == "adm_ball":
        await safe_edit(query, " Global Broadcast: <code>/broadcastall [msg]</code>", reply_markup=back)
    elif data == "adm_media":
        await safe_edit(query, "📻 Media Broadcast: Reply with <code>/broadcast_media</code>", reply_markup=back)
    elif data == "adm_user":
        await safe_edit(query, " User DM: <code>/broadcastuser [id] [msg]</code>", reply_markup=back)
    elif data == "adm_group":
        await safe_edit(query, " Group DM: <code>/broadcast [id] [msg]</code>", reply_markup=back)
    elif data == "adm_gmanage":
        text = (
            "🛡️ <b>Remote Group Management</b>\n\n"
            "Use these commands in any chat (I must be admin):\n"
            "├ 🔇 <code>/s_mute [gid] [uid]</code>\n"
            ""
            "├ 🔊 <code>/s_unmute [gid] [uid]</code>\n"
            "├ 👞 <code>/s_kick [gid] [uid]</code>\n"
            "└ 🚫 <code>/s_ban [gid] [uid]</code>"
        )
        await safe_edit(query, text, reply_markup=back)
    elif data == "adm_stats":
        await cmd_stats(update, context)

    elif data == "btn_hinata":
        context.user_data[AWAIT_HINATA] = True
        await safe_edit(query, "🌸 <b>Hinata Uncensored AI:</b>\n\n<i>Go ahead, talk to me...</i>", reply_markup=back)
    elif data == "btn_imagine":
        context.user_data[AWAIT_IMAGINE] = True
        await safe_edit(query, "🎨 <b>AI Image Studio:</b>\n\n⌨️ Enter your image prompt:", reply_markup=back)
    elif data == "btn_copilot":
        context.user_data[AWAIT_COPILOT] = True
        await safe_edit(query, "💡 <b>Copilot Thinking Hub:</b>\n\n⚡ Enter your complex query for deep analysis:", reply_markup=back)
    elif data == "btn_chatgpt":
        context.user_data[AWAIT_CHATGPT] = True 
        await safe_edit(query, "🤖 <b>GPT-5 Ultra Core:</b>\n\n⚡ Enter your message:", reply_markup=back)
    elif data == "btn_dolphin":
        context.user_data[AWAIT_DOLPHIN] = True
        await safe_edit(query, "🐬 <b>Dolphin Unrestricted:</b>\n\n⚡ Enter your message:", reply_markup=back)
    elif data == "btn_mistral":
        context.user_data[AWAIT_MISTRAL] = True
        await safe_edit(query, "🌪 <b>Mistral 3.1:</b>\n\n⚡ Enter your message:", reply_markup=back)
    elif data == "btn_zerotwo":
        context.user_data[AWAIT_ZEROTWO] = True
        await safe_edit(query, "💕 <b>Zero Two:</b>\n\nHey darling... tell me what's on your mind~", reply_markup=back)
    elif data == "btn_granite":
        context.user_data[AWAIT_GRANITE] = True
        await safe_edit(query, "💎 <b>Granite 4.0:</b>\n\n⚡ Enter your message:", reply_markup=back)
    elif data == "btn_llama4":
        context.user_data[AWAIT_LLAMA4] = True
        await safe_edit(query, "🦙 <b>Llama 4:</b>\n\n⚡ Enter your message:", reply_markup=back)
    elif data == "btn_ttstalk":
        context.user_data[AWAIT_TTSTALK] = True
        await safe_edit(query, "📱 <b>TikTok Intel Stalker:</b>\n\n⚡ Enter TikTok Username:", reply_markup=back)
    elif data == "btn_webzip_req":
        context.user_data[AWAIT_WEBZIP] = True
        await safe_edit(query, "📦 <b>Web to Zip:</b>\n\n🔗 Enter the URL to zip:", reply_markup=back)
    elif data == "btn_keeper_add":
        context.user_data[AWAIT_KEEPER_ADD] = True
        await safe_edit(query, "✅ <b>Uptime Keeper Add:</b>\n\n🔗 Enter URL (and optionally interval in mins, e.g. 'https://example.com 5'):", reply_markup=back)
    elif data == "btn_keeper_del":
        context.user_data[AWAIT_KEEPER_DEL] = True
        await safe_edit(query, "❌ <b>Uptime Keeper Delete:</b>\n\n🔗 Enter URL to remove:", reply_markup=back)
    elif data == "btn_center":
        text = (
            "✨ <b>HINATA NEURAL CENTER</b>\n"
            "──────────────────\n"
            "👤 <b>Developer:</b> @ShawonXnone\n"
            "📢 <b>Update Channel:</b> @Shawon_28\n"
            "🤖 <b>Bot Intelligence:</b> Hinata v3.0\n"
            "🏢 <b>Neural Status:</b> Online\n\n"
            "<i>Stay connected with our official nodes:</i>"
        )
        await safe_edit(query, text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Developer Profile", url="https://t.me/ShawonXnone")],
            [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/Shawon_28")],
            [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
        ]))
    elif data in ["btn_tera_req", "btn_mf_req"]:
        context.user_data[AWAIT_DL] = True
        await safe_edit(query, "📥 <b>Neural Downloader Interface:</b>\n\n⚡ Please send the URL to initiate extraction:", reply_markup=back)
    elif data.startswith("ytdl_"):
        parts = data.split("|")
        v_url = parts[1]
        v_type = parts[0].split("_")[1] # vid or aud
        context.user_data['ytdl_type_override'] = v_type
        await query.message.delete()
        # Mock message text to reuse download_media correctly
        query.message.text = v_url
        await download_media(update, context, v_url)
    elif data == "btn_pinterest":
        context.user_data[AWAIT_PINTEREST] = True
        await safe_edit(query, "📌 <b>Pinterest Discovery:</b>\n\nEnter what you want to search for:", reply_markup=back)
    elif data == "btn_ytdl_req":
        context.user_data[AWAIT_DL] = True
        await safe_edit(query, "🎬 <b>YouTube Downloader:</b>\n\n🔗 Enter the YouTube Video/Shorts URL:", reply_markup=back)
    elif data == "btn_instadl_req":
        context.user_data[AWAIT_DL] = True
        await safe_edit(query, "📸 <b>Instagram Downloader:</b>\n\n🔗 Enter the Instagram Post/Reel/IGTV URL:", reply_markup=back)
    elif data == "btn_ttdl_req":
        context.user_data[AWAIT_DL] = True
        await safe_edit(query, "📱 <b>TikTok Downloader:</b>\n\n🔗 Enter the TikTok Video/Photo URL:", reply_markup=back)
    elif data == "btn_pindl_req":
        context.user_data[AWAIT_DL] = True
        await safe_edit(query, "📌 <b>Pinterest Downloader:</b>\n\n🔗 Enter the Pinterest Image/Video URL:", reply_markup=back)
    elif data == "btn_rps": await cmd_game_rps(update, context)
    elif data == "btn_tod":
        await cmd_truthordare(update, context)
    elif data == "btn_slot":
        await cmd_game_slot(update, context)
    elif data == "btn_trivia":
        await cmd_game_trivia(update, context)
    elif data == "btn_lyrics":
        context.user_data[AWAIT_LYRICS] = True
        await safe_edit(query, "🎵 <b>AI Lyrics Finder:</b>\n\nEnter the song name and artist:", reply_markup=back)
    elif data == "btn_write":
        context.user_data[AWAIT_WRITE] = True
        await safe_edit(query, "✍️ <b>AI Creative Writer:</b>\n\nEnter the topic you want me to write about:", reply_markup=back)
    elif data == "btn_ask":
        context.user_data[AWAIT_ASK] = True
        await safe_edit(query, "❓ <b>AI Question Hub:</b>\n\nEnter your question:", reply_markup=back)
    elif data == "btn_bio":
        context.user_data[AWAIT_BIO] = True
        await safe_edit(query, "👤 <b>AI Bio Generator:</b>\n\nEnter some details about yourself:", reply_markup=back)
    elif data == "btn_tempmail":
        await cmd_tempmail(update, context)
    elif data == "btn_owner_info":
        owner_text = (
            "👑 <b>Owner Information</b>\n\n"
            "👤 <b>Name:</b> Shawon\n"
            "🆔 <b>Handle:</b> @ShawonXnone\n"
            "🌍 <b>Region:</b> Bangladesh\n"
            "🛠️ <b>Role:</b> Lead Developer\n\n"
            "<i>Feel free to contact for support or custom bot development.</i>"
        )
        await safe_edit(query, owner_text, reply_markup=back)
    elif data == "btn_back":
        await safe_edit(query, "🌸 <b>Main Control Center</b>\n\nChoose a category to explore my capabilities:", reply_markup=get_main_menu("home", query.from_user.id))
    elif data == "btn_wallpaper":
        await do_wallpaper_menu(update, context)
    elif data.startswith("wallgen_"):
        await do_wallpaper_gen(update, context, data.replace("wallgen_", ""))
    elif data == "btn_randomgirl":
        await do_random_girl(update, context)
    elif data == "btn_randompfp":
        await do_random_pfp(update, context)
    elif data == "btn_textmaker":
        await do_textmaker_menu(update, context)
    elif data.startswith("txtstyle_"):
        await handle_textmaker_style(update, context, data.replace("txtstyle_", ""))
    elif data.startswith("think_req|"):
        query_text = unquote(data.split("|")[1])
        msg = await update.effective_message.reply_text("💡 <b>Thinking Deeper...</b>", parse_mode="HTML")
        async with httpx.AsyncClient() as client:
            reply = await fetch_copilot(client, query_text)
        await msg.edit_text(reply, parse_mode="HTML")
    elif data.startswith("yt_dl_req|"):
        url = data.split("|")[1]
        await download_media(update, context, url)
    elif data == "btn_styletext_req":
        await cmd_styletext(update, context)
    elif data.startswith("style_pick|"):
        idx = int(data.split("|")[1])
        styles = context.user_data.get('temp_styles', [])
        if idx < len(styles):
            picked = styles[idx]
            await query.answer("✨ Style Selected!")
            await update.effective_message.reply_text(f"✅ <b>Styled Text (Click to copy):</b>\n\n<code>{html.escape(picked)}</code>", parse_mode="HTML")
        else:
            await query.answer("❌ Session expired. Please try again.", show_alert=True)
    elif data == "tm_refresh":
        await temp_mail_refresh(update, context, manual=True)
    elif data == "tm_close":
        context.user_data.pop('temp_mail', None)
        await safe_edit(query, "👋 <b>Temp Mail Session Closed.</b>")
    elif data == "btn_back":
        await safe_edit(query, "🌸 <b>Main Control Center</b>\n\nChoose a category to explore my capabilities:", reply_markup=get_main_menu("home", query.from_user.id))
    elif data.startswith("dl_fmt|"):
        _, fmt_id, ext = data.split("|")
        await process_download(update, context, fmt_id, ext)
    elif data.startswith("tod_"):
        mode = data.replace("tod_", "") # truth_funny, dare_hard, etc.
        await do_tod_fetch(update, context, mode)

async def do_tod_fetch(update: Update, _context: ContextTypes.DEFAULT_TYPE, mode: str):
    query = update.callback_query
    
    # mode is just 'truth' or 'dare' now
    await safe_edit(query, f" <b>Generating {mode.title()}...</b>")
    
    prompt = f"Generate a creative and engaging {mode} for a Truth or Dare game. Return only the {mode} text."
    async with httpx.AsyncClient() as client:
        reply = await fetch_chatgpt(client, prompt)
    
    kb = [
        [InlineKeyboardButton(" Roll Again", callback_data=f"tod_{mode}"),
         InlineKeyboardButton(" Back", callback_data="btn_back")]
    ]
    await safe_edit(query, f" <b>{mode.title()}:</b>\n\n{html.escape(reply)}", reply_markup=InlineKeyboardMarkup(kb))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user: return
    ud = context.user_data
    txt = msg.text or ""

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(" Back to Menu", callback_data="btn_back")]])

    if await check_permission(update, context, silent=True):
        # Trigger Hinata if 'hinata' is mentioned, or if user is directly replying to the bot in a group.
        # In a private chat, she always responds to every message
        mentioned = "hinata" in txt.lower()
        is_private = msg.chat.type == "private"
        is_reply_to_bot = bool(msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.id == context.bot.id)
        
        trigger_hinata = mentioned or is_reply_to_bot or is_private
        
        if trigger_hinata and not any(ud.get(key) for key in [AWAIT_GEMINI, AWAIT_IMAGINE, AWAIT_DEEPSEEK, AWAIT_FLIRT, AWAIT_HINATA, AWAIT_CODE, 'await_textmaker_input', AWAIT_CHATGPT, AWAIT_LYRICS, AWAIT_WRITE, AWAIT_ASK, AWAIT_BIO, AWAIT_COPILOT, AWAIT_INSTA, AWAIT_USERINFO, AWAIT_TTSTALK, AWAIT_FF, AWAIT_SHORTEN, AWAIT_EMAIL, AWAIT_PINTEREST, AWAIT_YTSEARCH, AWAIT_STYLETEXT, AWAIT_DL, AWAIT_QRGEN, AWAIT_TRANSLATE, AWAIT_SUMMARIZE, AWAIT_GRAMMAR, AWAIT_GUESS, AWAIT_RIDDLE, AWAIT_TRIVIA]):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            async with httpx.AsyncClient() as c: 
                r = await fetch_hinata(c, txt, update)
            await msg.reply_text(r, parse_mode="HTML")
            return

        if ud.pop(AWAIT_GEMINI, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("✨ <b>Analyzing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_gemini3(c, txt)
            await m.edit_text(f"🧠 <b>Gemini:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return

        if ud.pop(AWAIT_IMAGINE, False):
            context.args = txt.split()
            await cmd_imagine(update, context)
            return

        if ud.pop(AWAIT_DEEPSEEK, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🔥 <b>Searching...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_deepseek(c, txt)
            await m.edit_text(f"🔥 <b>DeepSeek:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_FLIRT, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("💖 <b>Thinking...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_flirt(c, txt)
            await m.edit_text(f"💖 <b>Flirt AI:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_HINATA, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🌸 <b>Hinata is typing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_hinata(c, txt, update)
            await m.edit_text(f"🌸 <b>Hinata:</b>\n\n{r}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_CODE, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("👨‍💻 <b>Coding...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_code(c, txt)
            # Ensure code blocks are used for copying
            if "```" not in r:
                r = f"```python\n{r}\n```"
            
            if len(r) > 4000:
                filename = "generated_code.py"
                with open(filename, "w", encoding="utf-8") as f:
                    code_content = r.replace("```python", "").replace("```", "").replace("👨‍💻", "").strip()
                    f.write(code_content)
                await msg.reply_document(document=open(filename, "rb"), caption="👨‍💻 <b>Code generated:</b>\n<i>Output was too large, so it was sent as a file.</i>", parse_mode="HTML", reply_markup=back_btn)
                await m.delete()
                os.remove(filename)
            else:
                await m.edit_text(f"👨‍💻 <b>Code AI:</b>\n\n{r}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop('await_textmaker_input', False):
            await do_textmaker_gen(update, context, txt.strip())
            return
        if ud.pop(AWAIT_CHATGPT, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🤖 <b>Connecting to GPT-5 Ultra...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_chatgpt(c, txt, chat_id=update.effective_chat.id, user_id=update.effective_user.id)
            await m.edit_text(f"🤖 <b>GPT-5 Ultra:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return

        elif ud.pop(AWAIT_DOLPHIN, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🐬 <b>Dolphin is generating...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_dolphin(c, txt)
            await m.edit_text(f"🐬 <b>Dolphin Unrestricted:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_MISTRAL, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🌪 <b>Mistral is generating...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_mistral(c, txt)
            await m.edit_text(f"🌪 <b>Mistral 3.1:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_ZEROTWO, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("💕 <b>Zero Two is typing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_zerotwo(c, txt)
            await m.edit_text(f"💕 <b>Zero Two:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return

        elif ud.pop(AWAIT_GRANITE, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("💎 <b>Granite 4.0 is thinking...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_granite(c, txt)
            await m.edit_text(f"💎 <b>Granite 4.0:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_LLAMA4, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🦙 <b>Llama 4 is analyzing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_llama4(c, txt)
            await m.edit_text(f"🦙 <b>Llama 4:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_WEBZIP, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("📦 <b>Zipping website... this might take a moment.</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c:
                try:
                    url = SAVE_WEB_ZIP_API.format(url=quote(txt.strip()))
                    resp = await c.get(url, timeout=60.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        dl_url = data.get("result") or data.get("url") or data.get("download_url") if isinstance(data, dict) else None
                        if dl_url:
                            await m.edit_text(f"📦 <b>Web to Zip Successful!</b>\n\n📥 You can download your zipped website here: {dl_url}", parse_mode="HTML")
                        else:
                            await m.edit_text("❌ Failed to parse zip link from the API.", parse_mode="HTML")
                    else:
                        await m.edit_text(f"❌ <b>Error:</b> API returned {resp.status_code}", parse_mode="HTML")
                except Exception as e:
                    await m.edit_text(f"❌ <b>Error:</b> {e}", parse_mode="HTML")
            return
            
        elif ud.pop(AWAIT_KEEPER_ADD, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("✅ <b>Adding to Uptime Service Keeper...</b>", parse_mode="HTML")
            parts = txt.strip().split()
            target_url = parts[0]
            interval = parts[1] if len(parts) > 1 else "5"
            if not target_url.startswith("http"): target_url = "http://" + target_url
            
            api_url = f"https://service-keeper-1.onrender.com/api/add?url={quote(target_url)}&interval={quote(interval)}"
            async with httpx.AsyncClient() as c:
                try:
                    resp = await c.get(api_url, timeout=20.0)
                    if resp.status_code == 200:
                        await m.edit_text(f"✅ <b>Successfully added to Keeper!</b>\n\n🔗 <b>URL:</b> {html.escape(target_url)}\n⏱️ <b>Interval:</b> {interval} mins", parse_mode="HTML", reply_markup=back_btn)
                    else:
                        await m.edit_text(f"❌ <b>Keeper Error:</b> API returned {resp.status_code}\n\n{resp.text}", parse_mode="HTML", reply_markup=back_btn)
                except Exception as e:
                    await m.edit_text(f"❌ <b>Keeper Error:</b> {e}", parse_mode="HTML", reply_markup=back_btn)
            return
            
        elif ud.pop(AWAIT_KEEPER_DEL, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("❌ <b>Removing from Uptime Service Keeper...</b>", parse_mode="HTML")
            target_url = txt.strip()
            if not target_url.startswith("http"): target_url = "http://" + target_url
            
            api_url = f"https://service-keeper-1.onrender.com/api/delete?url={quote(target_url)}"
            async with httpx.AsyncClient() as c:
                try:
                    resp = await c.get(api_url, timeout=20.0)
                    if resp.status_code == 200:
                        await m.edit_text(f"❌ <b>Successfully removed from Keeper!</b>\n\n🔗 <b>URL:</b> {html.escape(target_url)}", parse_mode="HTML", reply_markup=back_btn)
                    else:
                        await m.edit_text(f"❌ <b>Keeper Error:</b> API returned {resp.status_code}\n\n{resp.text}", parse_mode="HTML", reply_markup=back_btn)
                except Exception as e:
                    await m.edit_text(f"❌ <b>Keeper Error:</b> {e}", parse_mode="HTML", reply_markup=back_btn)
            return

        elif ud.pop(AWAIT_LYRICS, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🎵 <b>Searching for lyrics...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_lyrics(c, txt)
            await m.edit_text(f"🎵 <b>Lyrics Finder:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_WRITE, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("✍️ <b>Writing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_write(c, txt)
            await m.edit_text(f"✍️ <b>Creative Writer:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_ASK, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("❓ <b>Thinking...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_ask(c, txt)
            await m.edit_text(f"❓ <b>Question Hub:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_BIO, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("👤 <b>Generating bio...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_bio(c, txt)
            await m.edit_text(f"👤 <b>Bio Generator:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return

        elif ud.pop(AWAIT_COPILOT, False):
            m = await msg.reply_text("💡 <b>Thinking Deeply...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_copilot(c, txt)
            await m.edit_text(r, parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_POEM, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("📜 <b>Drafting Poem...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_poem(c, txt)
            await m.edit_text(f"📜 <b>Poem Master:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_STORY, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("✍️ <b>Crafting Story...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_story(c, txt)
            await m.edit_text(f"✍️ <b>Story AI:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_ADVICE, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("💡 <b>Pondering...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_advice(c, txt)
            await m.edit_text(f"💡 <b>Advice Hub:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_ROAST, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("🔥 <b>Preparing Roast...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_roast(c, txt)
            await m.edit_text(f"🔥 <b>Brutal Roast:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_JOKE, False):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            m = await msg.reply_text("😂 <b>Thinking of a joke...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_joke(c, txt)
            await m.edit_text(f"😂 <b>AI Joke:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_INSTA, False): await do_insta_fetch_by_text(update, context, txt.strip()); return
        elif ud.pop(AWAIT_USERINFO, False): await do_user_info_fetch(update, context, txt.strip()); return
        elif ud.pop(AWAIT_TTSTALK, False): await do_tt_stalk(update, context, txt.strip()); return
        elif ud.pop(AWAIT_FF, False): await do_ff_fetch_by_text(update, context, txt.strip()); return
        elif ud.pop(AWAIT_SHORTEN, False):
            context.args = txt.split()
            await cmd_shorten(update, context)
            return
        elif ud.pop(AWAIT_EMAIL, False):
            context.args = txt.split()
            await cmd_email(update, context)
            return
        elif ud.pop(AWAIT_PINTEREST, False):
            context.args = txt.split()
            await cmd_pinterest(update, context)
            return
        elif ud.pop(AWAIT_YTSEARCH, False):
            context.args = txt.split()
            await cmd_ytsearch(update, context)
            return
        elif ud.pop(AWAIT_STYLETEXT, False):
            context.args = txt.split()
            await cmd_styletext(update, context)
            return
        elif ud.pop(AWAIT_DL, False): await download_media(update, context, txt.strip()); return
        elif ud.pop(AWAIT_QRGEN, False): await cmd_qrgen(update, context); return
        elif ud.pop(AWAIT_TRANSLATE, False): 
            context.args = txt.split()
            await cmd_translate(update, context)
            return
        elif ud.pop(AWAIT_SUMMARIZE, False): 
            context.args = txt.split()
            await cmd_summarize(update, context)
            return
        elif ud.pop(AWAIT_GRAMMAR, False):
            m = await msg.reply_text("🔡 <b>Analyzing Grammar...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_grammar(c, txt)
            await m.edit_text(f"🔡 <b>Corrected Text:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_GUESS, False):
            try:
                guess = int(txt.strip())
                secret = ud.get("guess_num")
                attempts = ud.get("guess_attempts", 0) + 1
                ud["guess_attempts"] = attempts
                
                if guess == secret:
                    await msg.reply_text(f"✅ <b>Correct!</b> The number was <code>{secret}</code>. It took you {attempts} tries!", parse_mode="HTML", reply_markup=back_btn)
                    ud.pop("guess_num", None)
                    ud.pop("guess_attempts", None)
                elif guess < secret:
                    ud[AWAIT_GUESS] = True
                    await msg.reply_text("🔼 <b>Higher!</b> Try again:", parse_mode="HTML")
                else:
                    ud[AWAIT_GUESS] = True
                    await msg.reply_text("🔽 <b>Lower!</b> Try again:", parse_mode="HTML")
            except:
                ud[AWAIT_GUESS] = True
                await msg.reply_text("⚠️ Please enter a valid number.")
            return
        elif ud.pop(AWAIT_RIDDLE, False):
            answer = ud.get("riddle_answer", "").lower()
            if txt.strip().lower() in answer or balance_check(txt.strip().lower(), answer):
                await msg.reply_text(f"🌟 <b>Perfect!</b> You got it right.\n\nAnswer: <code>{ud.get('riddle_answer')}</code>", parse_mode="HTML", reply_markup=back_btn)
            else:
                await msg.reply_text(f"❌ <b>Wrong!</b>\n\nThe correct answer was: <code>{ud.get('riddle_answer')}</code>", parse_mode="HTML", reply_markup=back_btn)
            ud.pop("riddle_answer", None)
            return
        elif ud.pop(AWAIT_TRIVIA, False):
            secret = ud.get("trivia_answer", "").lower()
            guess = txt.strip().lower()
            if guess == secret or secret in guess: # Simple loose match
                await msg.reply_text(f"🎉 <b>Correct!</b>\n\nAnswer: <code>{ud.get('trivia_answer')}</code>", parse_mode="HTML", reply_markup=back_btn)
            else:
                await msg.reply_text(f"❌ <b>Incorrect!</b>\n\nThe right answer was: <code>{ud.get('trivia_answer')}</code>", parse_mode="HTML", reply_markup=back_btn)
            ud.pop("trivia_answer", None)
            return
        elif ud.pop(AWAIT_BGREM, False):
            if msg.photo: await do_bg_remove(update, context)
            else: await msg.reply_text("📸 <b>Please send a photo</b> to remove its background.", parse_mode="HTML")
            return
        elif ud.pop(AWAIT_DETECTOR, False):
            context.args = [txt]
            await cmd_detector(update, context)
            return
        elif ud.pop(AWAIT_WEBSS, False):
            context.args = [txt]
            await cmd_webss(update, context)
            return
    
    if msg.chat.type == "private": 
        await forward_or_copy(update, context)

    

async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.my_chat_member.chat
    if chat.type in ["group", "supergroup"]:
        database.add_group(chat.id, chat.title, chat.type)



async def group_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await update.effective_message.reply_text(f"✨ 👤 User <code>{user_id}</code> banned from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.effective_message.reply_text(f"✨ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
        await update.effective_message.reply_text(f"✨ 👤 User <code>{user_id}</code> unbanned from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.effective_message.reply_text(f"✨ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=False))
        await update.effective_message.reply_text(f" 👤 User <code>{user_id}</code> 🔇 muted in <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.effective_message.reply_text(f"✨ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=True, can_invite_users=True, can_pin_messages=True))
        await update.effective_message.reply_text(f" 👤 User <code>{user_id}</code> 🔊 un🔇 muted in <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.effective_message.reply_text(f"✨ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        await update.effective_message.reply_text(f" 👤 User <code>{user_id}</code> 👞 kicked from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.effective_message.reply_text(f"✨ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a user as admin in a specific chat. Usage: /s_addadmin [chat_id] [user_id]"""
    if not is_owner(update.effective_user.id):
        return
    
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            " <b>Usage:</b> <code>/s_addadmin [chat_id] [user_id]</code>\n\n"
            "<i>Example: /s_addadmin -1001234567890 7333244376</i>",
            parse_mode="HTML"
        )
        return
    
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        
        # Promote user to admin with full permissions
        await context.bot.promote_chat_member(
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
        
        await update.effective_message.reply_text(
            f"✨ <b>Admin Promotion Successful!</b>\n\n"
            f" <b>User ID:</b> <code>{user_id}</code>\n"
            f" <b>Chat ID:</b> <code>{chat_id}</code>\n\n"
            f"<i>User has been granted full admin privileges.</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.effective_message.reply_text(
            f"✨ <b>Failed to add admin:</b>\n<code>{html.escape(str(e))}</code>",
            parse_mode="HTML"
        )

async def broadcastall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or not context.args: return
    text = " ".join(context.args)
    users = database.get_all_users()
    groups = database.get_all_groups()
    
    s = f = 0
    msg_ids_map = {}
    
    status_msg = await update.effective_message.reply_text("🚀 <b>Global Broadcast Initiated...</b>", parse_mode="HTML")
    
    # Send to Users
    for u in users:
        uid = u.get('id')
        try:
            sent = await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            save_broadcast_msg(sent.chat_id, sent.message_id)
            msg_ids_map[str(sent.chat_id)] = sent.message_id
            s += 1
        except:
            f += 1
            
    # Send to Groups
    for g in groups:
        gid = g.get('id')
        try:
            sent = await context.bot.send_message(chat_id=gid, text=text, parse_mode="HTML")
            save_broadcast_msg(sent.chat_id, sent.message_id)
            msg_ids_map[str(sent.chat_id)] = sent.message_id
            s += 1
        except:
            f += 1
            
    # Save to DB
    database.add_broadcast(text, "all", s, f, msg_ids_map)
    STATS["broadcasts"] += 1
    await status_msg.edit_text(f"✨ <b>Broadcast Complete</b>\n\n✅ <b>Sent:</b> {s}\n❌ <b>Failed:</b> {f}", parse_mode="HTML")
    update_stats(sent_users=s, failed_users=f)

async def broadcast_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message to a specific user ID or the user being replied to."""
    if not is_owner(update.effective_user.id): return
    
    target_id = None
    text = ""
    
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        text = " ".join(context.args) if context.args else ""
    elif context.args:
        try:
            target_id = int(context.args[0])
            text = " ".join(context.args[1:])
        except: pass
        
    if not target_id or not text:
        await update.effective_message.reply_text("💡 <b>Usage:</b> <code>/broadcastuser [id] [msg]</code> or reply to a user with <code>/broadcastuser [msg]</code>", parse_mode="HTML")
        return
        
    try:
        sent = await context.bot.send_message(chat_id=target_id, text=text, parse_mode="HTML")
        save_broadcast_msg(sent.chat_id, sent.message_id)
        database.add_broadcast(text, "user", 1, 0, {str(sent.chat_id): sent.message_id})
        STATS["broadcasts"] += 1
        await update.effective_message.reply_text(f"✅ <b>Message Sent to User:</b> <code>{target_id}</code>", parse_mode="HTML")
        update_stats(sent_users=1)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ <b>Delivery Failed:</b>\n<code>{e}</code>", parse_mode="HTML")
        update_stats(failed_users=1)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message to a specific group/chat ID or the group being replied to."""
    if not is_owner(update.effective_user.id): return
    
    target_id = None
    text = ""
    
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.chat_id
        text = " ".join(context.args) if context.args else ""
    elif context.args:
        try:
            target_id = int(context.args[0])
            text = " ".join(context.args[1:])
        except: pass

    if not target_id or not text:
        await update.effective_message.reply_text("💡 <b>Usage:</b> <code>/broadcast [id] [msg]</code> or reply to a message in a group with <code>/broadcast [msg]</code>", parse_mode="HTML")
        return
        
    try:
        sent = await context.bot.send_message(chat_id=target_id, text=text, parse_mode="HTML")
        save_broadcast_msg(sent.chat_id, sent.message_id)
        database.add_broadcast(text, "specific", 1, 0, {str(sent.chat_id): sent.message_id})
        STATS["broadcasts"] += 1
        await update.effective_message.reply_text(f"✨ <b>Broadcast Sent to Chat:</b> <code>{target_id}</code>", parse_mode="HTML")
        update_stats(sent_groups=1)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ <b>Group Delivery Failed:</b>\n<code>{e}</code>", parse_mode="HTML")
        update_stats(failed_groups=1)


async def broadcast_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    msg = update.message
    photo = None
    if msg.reply_to_message and (msg.reply_to_message.photo or msg.reply_to_message.document):
        photo = msg.reply_to_message.photo[-1].file_id if msg.reply_to_message.photo else msg.reply_to_message.document.file_id
        cap = " ".join(context.args) if context.args else (msg.reply_to_message.caption or "")
    elif msg.photo:
        photo = msg.photo[-1].file_id
        cap = msg.caption or ""
    else:
        return
    gs = database.get_all_groups()
    s = f = 0
    msg_ids_map = {}
    for g in gs:
        gid = g.get('id') if isinstance(g, dict) else g
        try:
            sent = await context.bot.send_photo(chat_id=gid, photo=photo, caption=cap, parse_mode="HTML")
            save_broadcast_msg(sent.chat_id, sent.message_id)
            msg_ids_map[str(sent.chat_id)] = sent.message_id
            s += 1
        except:
            f += 1
            
    # Save to DB
    database.add_broadcast(f"[Media] {cap[:50]}...", "groups", s, f, msg_ids_map)
    STATS["broadcasts"] += 1
    await msg.reply_text(f"✨ Media Blast: ✨ {s} | ✨ {f}")
    update_stats(sent_groups=s, failed_groups=f)

async def cmd_del_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    history = read_json("broadcast_history.json", [])
    if not history:
        return
    
    status_msg = await update.effective_message.reply_text(f"✨ <b>Cleaning up {len(history)} messages...</b>", parse_mode="HTML")
    s = f = 0
    for entry in history:
        try:
            await context.bot.delete_message(chat_id=entry['chat_id'], message_id=entry['message_id'])
            s += 1
        except Exception:
            f += 1
            
    # Clear history after attempt
    write_json("broadcast_history.json", [])
    await status_msg.edit_text(f"✨ <b>Cleanup Complete</b>\n\n✨ Deleted: {s}\n Failed: {f}", parse_mode="HTML")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and handle common Telegram API issues."""
    err = context.error
    if isinstance(err, Forbidden):
        return # Bot blocked
    if isinstance(err, BadRequest):
        err_msg = str(err)
        if "Message to be replied not found" in err_msg or "Message to edit not found" in err_msg or "Message is not modified" in err_msg:
            return
    
    logger.error(f"Update {update} caused error {err}")
    # Optional: notify owner for critical errors
    if not isinstance(err, (BadRequest, Forbidden)):
        try:
            await context.bot.send_message(chat_id=OWNER_ID, text=f" <b>Bot Error:</b>\n<code>{html.escape(str(err))[:500]}</code>", parse_mode="HTML")
        except: pass

# ================= Background Cleanup =================
async def auto_cleanup_task():
    """Wipes the downloads folder every 10 minutes and clears log file if too large."""
    while True:
        try:
            # Clear downloads folder
            if os.path.exists("downloads"):
                files_removed = 0
                for f in os.listdir("downloads"):
                    path = os.path.join("downloads", f)
                    try:
                        if os.path.isfile(path): 
                            os.remove(path)
                            files_removed += 1
                        elif os.path.isdir(path): 
                            shutil.rmtree(path)
                            files_removed += 1
                    except: pass
                if files_removed > 0:
                    logger.info(f"Auto-cleanup: {files_removed} items removed from downloads folder.")
            
            # Clear log file if it exceeds MAX_LOG_SIZE
            if os.path.exists(LOG_FILE):
                log_size = os.path.getsize(LOG_FILE)
                if log_size > MAX_LOG_SIZE:
                    # Keep only the last 50KB of logs
                    try:
                        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(max(0, log_size - 50 * 1024))
                            f.readline()  # Skip partial line
                            remaining_logs = f.read()
                        
                        with open(LOG_FILE, 'w', encoding='utf-8') as f:
                            f.write(f"[LOG TRUNCATED - Previous logs cleared at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n\n")
                            f.write(remaining_logs)
                        
                        logger.info(f"Auto-cleanup: Log file truncated from {log_size/1024:.1f}KB to ~50KB.")
                    except Exception as log_err:
                        logger.error(f"Failed to truncate log: {log_err}")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(600) # 10 minutes

# ================= Run =================
# Global application object for access from main.py
app = None

async def start_bot():
    global app, BOT_TOKEN
    BOT_TOKEN = read_file(BOT_TOKEN_FILE)
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return
        
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Auto-Register Commands
        cmds = [
            BotCommand("start", "Main Menu"),
            BotCommand("alive", "Sys Check"),
            BotCommand("ping", "Latency Test"),
            BotCommand("ai", "AI Features Hub"),
            BotCommand("gemini", "Gemini 3 Pro"),
            BotCommand("deepseek", "DeepSeek R1"),
            BotCommand("chatgpt", "GPT-5 Ultra"),
            BotCommand("copilot", "Think Deeper"),
            BotCommand("code", "Code Architect"),
            BotCommand("imagine", "Imagine Art"),
            BotCommand("translate", "AI Translator"),
            BotCommand("summarize", "AI Summarizer"),
            BotCommand("grammar", "Grammar Check"),
            BotCommand("detector", "AI Detector"),
            BotCommand("dl", "Media Downloader"),
            BotCommand("ytsearch", "YouTube Search"),
            BotCommand("pinterest", "Pinterest Search"),
            BotCommand("insta", "Insta Stalk"),
            BotCommand("ff", "Free Fire Stalk"),
            BotCommand("ttstalk", "TikTok Stalk"),
            BotCommand("tempmail", "Temp Mailbox"),
            BotCommand("email", "Secure Email"),
            BotCommand("shorten", "URL Shortener"),
            BotCommand("qrgen", "QR Generator"),
            BotCommand("qrread", "QR Scanner"),
            BotCommand("webss", "Web Screenshot"),
            BotCommand("bgrem", "BG Remover"),
            BotCommand("ttt", "Tic Tac Toe"),
            BotCommand("riddle", "Riddle Quest"),
            BotCommand("trivia", "Trivia Master"),
            BotCommand("truthordare", "Truth or Dare"),
            BotCommand("guess", "Guess Number"),
            BotCommand("slot", "Slot Machine"),
            BotCommand("rps", "Rock Paper Scissor"),
            BotCommand("stats", "Bot Metrics"),
            BotCommand("help", "AI Support Matrix")
        ]
        
        await app.initialize()
        try:
            await app.bot.set_my_commands(cmds)
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
            
        app.add_error_handler(error_handler)
    
        # Central Neural Tracker (High Priority)
        app.add_handler(TypeHandler(Update, global_neural_tracker), group=-1)

        app.add_handler(CommandHandler("insta", handle_insta_cmd))
        app.add_handler(CommandHandler("userinfo", handle_userinfo_cmd))
        app.add_handler(CommandHandler("id", handle_userinfo_cmd))
        app.add_handler(CommandHandler("ffstalk", handle_ff_cmd))
        app.add_handler(CommandHandler("ff", handle_ff_cmd))
        app.add_handler(CommandHandler("pinterest", cmd_pinterest))
        app.add_handler(CommandHandler("ytsearch", cmd_ytsearch))
        app.add_handler(CommandHandler("styletext", cmd_styletext))
        app.add_handler(CommandHandler("copilot", cmd_copilot))
        app.add_handler(CommandHandler("dl", handle_dl_cmd))
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("alive", cmd_alive))
        app.add_handler(CommandHandler("ping", cmd_ping))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("commands", cmd_commands))
        app.add_handler(CommandHandler("stats", cmd_stats))
        app.add_handler(CommandHandler("gemini", cmd_gemini))
        app.add_handler(CommandHandler("deepseek", cmd_deepseek))
        app.add_handler(CommandHandler("chatgpt", cmd_chatgpt))
        app.add_handler(CommandHandler("dolphin", cmd_dolphin))
        app.add_handler(CommandHandler("mistral", cmd_mistral))
        app.add_handler(CommandHandler("zerotwo", cmd_zerotwo))
        app.add_handler(CommandHandler("granite", cmd_granite))
        app.add_handler(CommandHandler("llama4", cmd_llama4))
        app.add_handler(CommandHandler("flirt", cmd_flirt))
        app.add_handler(CommandHandler("code", cmd_code))
        app.add_handler(CommandHandler("hinata", cmd_hinata))
        app.add_handler(CommandHandler("tempmail", cmd_tempmail))
        app.add_handler(CommandHandler("ai", cmd_ai_combined))
        app.add_handler(CommandHandler("qrgen", cmd_qrgen))
        app.add_handler(CommandHandler("qrread", cmd_qrread))
        app.add_handler(CommandHandler("webzip", cmd_webzip))
        app.add_handler(CommandHandler("webss", cmd_webss))
        app.add_handler(CommandHandler("bgrem", cmd_bgrem))
        app.add_handler(CommandHandler("translate", cmd_translate))
        app.add_handler(CommandHandler("summarize", cmd_summarize))
        app.add_handler(CommandHandler("grammar", cmd_grammar))
        app.add_handler(CommandHandler("tod", cmd_truthordare))
        app.add_handler(CommandHandler("rps", cmd_game_rps))
        app.add_handler(CommandHandler("coin", cmd_game_coin))
        app.add_handler(CommandHandler("slot", cmd_game_slot))
        app.add_handler(CommandHandler("dice", cmd_game_dice))
        app.add_handler(CommandHandler("ttt", cmd_game_ttt))
        app.add_handler(CommandHandler("shorten", cmd_shorten))
        app.add_handler(CommandHandler("guess", cmd_game_guess))
        app.add_handler(CommandHandler("riddle", cmd_game_riddle))
        app.add_handler(CommandHandler("trivia", cmd_game_trivia))
        app.add_handler(CommandHandler("imagine", cmd_imagine))
        
        # Admin Commands with 's_' prefix
        app.add_handler(CommandHandler("download_db", cmd_download_db))
        app.add_handler(CommandHandler("getdb", cmd_download_db))
        app.add_handler(CommandHandler("s_gban", cmd_gban))
        app.add_handler(CommandHandler("s_ungban", cmd_ungban))
        app.add_handler(CommandHandler("s_toggle_access", cmd_toggle_access))
        app.add_handler(CommandHandler("s_broadcastall", broadcastall))
        app.add_handler(CommandHandler("s_broadcastuser", broadcast_user))
        app.add_handler(CommandHandler("s_broadcast", broadcast))
        app.add_handler(CommandHandler("s_broadcast_media", broadcast_media))
        app.add_handler(CommandHandler("s_delbroadcast", cmd_del_broadcast))
        app.add_handler(CommandHandler("s_ban", group_ban))
        app.add_handler(CommandHandler("s_unban", group_unban))
        app.add_handler(CommandHandler("s_mute", group_mute))
        app.add_handler(CommandHandler("s_unmute", group_unmute))
        app.add_handler(CommandHandler("s_kick", group_kick))
        app.add_handler(CommandHandler("s_addadmin", cmd_addadmin))

        app.add_handler(CommandHandler("detector", cmd_detector))
        app.add_handler(CommandHandler("webss", cmd_webss))
        app.add_handler(CommandHandler("email", cmd_email))

        app.add_handler(CallbackQueryHandler(callback_handler))
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        
        # Catch-all to silently ignore any unknown commands
        async def ignore_unknown_cmds(update, context): pass
        app.add_handler(MessageHandler(filters.COMMAND, ignore_unknown_cmds))
        
        app.add_handler(ChatMemberHandler(track_group, ChatMemberHandler.MY_CHAT_MEMBER))
        
        logger.info("Hinata Initialized")
        
        await app.start()
        await app.updater.start_polling()
        STATS["status"] = "online"
        logger.info("Hinata Live and Polling")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        STATS["status"] = "offline"
        if "rejected by the server" in str(e).lower() or "unauthorized" in str(e).lower():
            logger.error("CRITICAL: Your Telegram Bot Token is INVALID. Please check @BotFather.")

    # Start cleanup task (runs regardless of bot connection)
    asyncio.create_task(auto_cleanup_task())



async def stop_bot():
    global app
    if app:
        try:
            if app.updater and app.updater.running:
                await app.updater.stop()
        except Exception as e:
            logger.error(f"Error stopping updater: {e}")
            
        try:
            await app.stop()
        except Exception as e:
            logger.error(f"Error stopping app: {e}")
            
        try:
            await app.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down app: {e}")
        
        app = None
        logger.info("Bot Stopped")
    STATS["status"] = "offline"

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
