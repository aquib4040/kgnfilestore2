# Import required libraries and modules
from bot import Bot
from pyrogram import Client, filters
from config import *
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
import re
import motor.motor_asyncio
from config import DB_URI, DB_NAME ,REFERTIME


dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']

channels_collection = database['channels']

# Retrieve all force subscription channels from the database
async def get_force_sub_channels():
    """Retrieve all force subscription channels from the database."""
    channels = await channels_collection.find({}).to_list(length=None)
    return [channel['channel_id'] for channel in channels]

async def get_all_force_sub_channels():
    """Retrieve all force subscription channels dynamically."""
    channels = await channels_collection.find({}).to_list(length=None)
    return [{"channel_id": channel["channel_id"]} for channel in channels]

# Add a new force subscription channel
async def add_channel(channel_id: int):
    """Add a new force subscription channel."""
    await channels_collection.update_one(
        {'channel_id': channel_id},
        {'$set': {'channel_id': channel_id}},
        upsert=True
    )

# Remove a force subscription channel
async def remove_channel(channel_id: int):
    """Remove a force subscription channel."""
    result = await channels_collection.delete_one({'channel_id': channel_id})
    return result

# List all force subscription channels
async def list_channels():
    """List all force subscription channels."""
    return await get_force_sub_channels()

# Reset all force subscription channels (clear the collection)
async def reset_channels():
    """Reset all force subscription channels (clear the collection)."""
    await channels_collection.delete_many({})


# Command: Add a new channel
@Client.on_message(filters.command("fadd") & filters.user(ADMINS))
async def add_channel_command(client: Client, message: Message):
    try:
        channel_id = int(message.text.split()[1])
        await add_channel(channel_id)
        await message.reply_text(f"✅ Channel {channel_id} added successfully.")
    except IndexError:
        await message.reply_text("❌ Please provide a channel ID: /fadd <channel_id>")
    except Exception as e:
        await message.reply_text(f"❌ Error adding channel: {e}")

# Command: Remove a channel
@Client.on_message(filters.command("fremove") & filters.user(ADMINS))
async def remove_channel_command(client: Client, message: Message):
    try:
        channel_id = int(message.text.split()[1])
        result = await remove_channel(channel_id)
        if result.deleted_count:
            await message.reply_text(f"✅ Channel {channel_id} removed successfully.")
        else:
            await message.reply_text(f"❌ Channel {channel_id} not found.")
    except IndexError:
        await message.reply_text("❌ Please provide a channel ID: /fremove <channel_id>")
    except Exception as e:
        await message.reply_text(f"❌ Error removing channel: {e}")

# Command: List all channels
@Client.on_message(filters.command("flist") & filters.user(ADMINS))
async def list_channels_command(client: Client, message: Message):
    try:
        channels = await list_channels()
        if not channels:
            await message.reply_text("❌ No channels configured.")
        else:
            channel_list = "\n".join([str(channel) for channel in channels])
            await message.reply_text(f"📜 Current channels:\n{channel_list}")
    except Exception as e:
        await message.reply_text(f"❌ Error listing channels: {e}")

# Command: Reset all channels (clear collection)
@Client.on_message(filters.command("freset") & filters.user(ADMINS))
async def reset_channels_command(client: Client, message: Message):
    try:
        await reset_channels()
        await message.reply_text("✅ All force subscription channels have been reset (cleared).")
    except Exception as e:
        await message.reply_text(f"❌ Error resetting channels: {e}")
