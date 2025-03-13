from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
import time
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode , ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, RPCError
from config import *
from plugins.cbb import *

mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]
channels_collection = db["force_sub_channels"]
database = db[DB_NAME]
user_data = database['users']
cmd_data = database['cmds']

FORCE_MSG = """╭𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝖲𝗍𝖺𝗍𝗎𝗌 :

{status_list}

𝖧𝖾𝗒 {mention}, 𝖯𝗅𝖾𝖺𝗌𝖾 𝖩𝗈𝗂𝗇 𝗆𝗒 𝖢𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝖺𝗇𝖽 𝗍𝗁𝖾𝗇 𝖼𝗅𝗂𝖼𝗄 𝗈𝗇 '↺𝖱𝖾𝖿𝗋𝖾𝗌h' 𝗍𝗈 𝗀𝖾𝗍 𝗒𝗈𝗎𝗋 𝖤𝗉𝗂𝗌𝗈𝖽𝖾'𝗌"""

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

async def is_subscribed(filter, client, update):
    user_id = update.from_user.id

    # Admins bypass subscription checks
    if user_id in ADMINS:
        return True

    # Get the list of force subscription channels
    force_sub_channels = await get_force_sub_channels()

    member_status = {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}

    for channel_id in force_sub_channels:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
        except UserNotParticipant:
            return False
        if member.status not in member_status:
            return False

    return True

@Client.on_message(filters.command("pstart") & filters.private)
async def not_joined(client: Client, message: Message):
    """Handles the force subscription feature."""
    user_id = message.from_user.id
    force_sub_channels = await get_force_sub_channels()  # Replace with your function to get the channel list.
    buttons = []
    status_list = []

    temp_buttons = []  # Temporary list to group buttons into rows of 2

    for i, channel_id in enumerate(force_sub_channels):
        try:
            # Fetch invite link and expiration info from the database
            invite_info = await channels_collection.find_one({"channel_id": channel_id})
            invite_link = invite_info.get("invite_link") if invite_info else None
            expires_at = invite_info.get("expires_at") if invite_info else None

            # Generate a new invite link if expired or not found
            if not invite_link or not expires_at or datetime.utcnow() > expires_at:
                new_invite_link = await client.export_chat_invite_link(channel_id)
                expires_in = timedelta(hours=1)
                expires_at = datetime.utcnow() + expires_in

                # Update the database
                await channels_collection.update_one(
                    {"channel_id": channel_id},
                    {"$set": {"invite_link": new_invite_link, "expires_at": expires_at}},
                    upsert=True,
                )
                invite_link = new_invite_link

            # Check user membership status
            try:
                member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status in {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}:
                    status_list.append(f"{i + 1}. Channel {i + 1} - ✅ 𝖩𝗈𝗂𝗇𝖾𝖽")
                else:
                    status_list.append(f"{i + 1}. Channel {i + 1} - ❌ 𝖭𝗈𝗍 𝖩𝗈𝗂𝗇𝖾𝖽")
                    temp_buttons.append(InlineKeyboardButton(f"Join Channel {i + 1}", url=invite_link))

            except UserNotParticipant:
                status_list.append(f"{i + 1}. Channel {i + 1} - ❌ 𝖭𝗈𝗍 𝖩𝗈𝗂𝗇𝖾𝖽")
                temp_buttons.append(InlineKeyboardButton(f"Join Channel {i + 1}", url=invite_link))
            except Exception as e:
                print(f"Error checking membership for {channel_id}: {e}")
                status_list.append(f"{i + 1}. Channel {i + 1} - ⚠️ Error")
                temp_buttons.append(InlineKeyboardButton(f"Join Channel {i + 1}", url=invite_link))

        except Exception as e:
            print(f"Error processing channel {channel_id}: {e}")
            status_list.append(f"{i + 1}. Channel {i + 1} - ⚠️ Error")
            temp_buttons.append(InlineKeyboardButton(f"Error < Help {i + 1}", url=f"https://t.me/{OWNER_USERNAME}"))

        # Append buttons in rows of 2
        if len(temp_buttons) == 2:
            buttons.append(temp_buttons)
            temp_buttons = []

    # Add any remaining buttons (less than 2)
    if temp_buttons:
        buttons.append(temp_buttons)

    # Add a "Refresh" button
    buttons.append([
        InlineKeyboardButton("↺ Refresh", callback_data="refresh_status"),
    ])
    '''
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='↺ Get File',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass
    '''
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='↺ Get File',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )

        last_cmd = message.command[1]
        
        # Update or insert the user's last command
        database.cmd_data.update_one(
            {"user_id": user_id},
            {"$set": {"last_cmd": last_cmd}},
            upsert=True
        )
    except IndexError:
        pass

    # Always use the same caption format without conditional
    caption = FORCE_MSG.format(status_list="\n".join(status_list), mention=message.from_user.mention)

    # Send the reply with buttons
    try:
        await message.reply_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True,
        )
    except Exception as e:
        print(f"Error sending reply: {e}")






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


subscribed = filters.create(is_subscribed)
