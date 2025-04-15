from pyrogram import Client, filters, enums
#from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.types import *
from pyrogram.enums import ParseMode, ChatMemberStatus
from datetime import datetime, timedelta
from config import *
from plugins.fsub import *
import random
from Script import script

# Callback query handler
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data
    mention = query.from_user.mention
    user_id = query.from_user.id

    try:
        if data == "aboutx":
            await query.message.edit_text(
                text=(
                    f"<b>○ Creator : <a href='tg://user?id={OWNER_ID}'>𝖲𝖺𝗂𝗇𝗍</a>\n"
                    f"○ Channel : @{CHANNEL}\n"
                    f"○ Support Group : @{SUPPORT_GROUP}</b>"
                ),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔒 Close", callback_data="close")]]
                )
            )
        elif data == "close":
            await query.message.delete()
            try:
                await query.message.reply_to_message.delete()
            except Exception as e:
                print(f"Error deleting reply-to message: {e}")
        
        elif query.data == "about":
            buttons = [[
                InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
                InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
            ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(buttons)
            me2 = (await client.get_me()).mention
            await query.message.edit_text(
                text=script.ABOUT_TXT.format(me2),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        elif query.data == "start":
            buttons = [[
            InlineKeyboardButton('💝 ᴊᴏɪɴ ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/+eKKOHxiwKv00MGM1'),
            InlineKeyboardButton('🎬 ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ', url='https://t.me/Ongoingmoviehub')
            ],[
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/+zlb3ReuJ40tjMDA1'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/KGN_BOT_Z')
            ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
            ]]
            if CLONE_MODE == True:
                buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            me2 = (await client.get_me()).mention
            await query.message.edit_text(
                text=script.START_TXT.format(query.from_user.mention, me2),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
    
        elif query.data == "clone":
            buttons = [[
                InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
                InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
            ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=script.CLONE_TXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )          

        
        elif query.data == "help":
            buttons = [[
                InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
                InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
            ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=script.HELP_TXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 

        elif data == "refresh_status":
            # Refresh force subscription status
            force_sub_channels = await get_force_sub_channels()
            buttons = []
            status_list = []

            last_cmd = await database.cmd_data.find_one({"user_id": user_id}, {"last_cmd": 1})  # Fetch the last command from the database
            last_cmd = last_cmd.get("last_cmd") if last_cmd else "default_cmd"  # Default value if no command is found

            for i, channel_id in enumerate(force_sub_channels):
                try:
                    invite_info = await channels_collection.find_one({"channel_id": channel_id})
                    invite_link = invite_info.get("invite_link") if invite_info else None
                    expires_at = invite_info.get("expires_at") if invite_info else None

                    if not invite_link or not expires_at or datetime.utcnow() > expires_at:
                        new_invite_link = await client.export_chat_invite_link(channel_id)
                        expires_in = timedelta(hours=1)
                        expires_at = datetime.utcnow() + expires_in

                        await channels_collection.update_one(
                            {"channel_id": channel_id},
                            {"$set": {"invite_link": new_invite_link, "expires_at": expires_at}},
                            upsert=True,
                        )
                        invite_link = new_invite_link

                    try:
                        member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
                        if member.status in {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}:
                            status_list.append(f"{i + 1}. Channel {i + 1} - ✅ Joined")
                        else:
                            status_list.append(f"{i + 1}. Channel {i + 1} - ❌ Not Joined")
                            buttons.append(InlineKeyboardButton(f"Join Channel {i + 1}", url=invite_link))
                    except Exception:
                        status_list.append(f"{i + 1}. Channel {i + 1} - ❌ Not Joined")
                        buttons.append(InlineKeyboardButton(f"Join Channel {i + 1}", url=invite_link))
                except Exception as e:
                    print(f"Error processing channel {channel_id}: {e}")
                    status_list.append(f"{i + 1}. Channel {i + 1} - ⚠️ Error")
                    buttons.append(InlineKeyboardButton(f"Error Help {i + 1}", url=f"https://t.me/{OWNER_USERNAME}"))

            try:
                # Add "Get File" button with last command
                buttons.append(InlineKeyboardButton(
                    text="↺ Get File",
                    url=f"https://t.me/{client.username}?start={last_cmd}"
                ))
            except IndexError:
                pass

            keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
            keyboard.append([InlineKeyboardButton("↺ Refresh", callback_data="refresh_status")])

            # Removed conditional part and replaced it with a single caption
            caption = FORCE_MSG.format(status_list="\n".join(status_list), mention=mention)

            await query.message.edit_text(
                text=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            await query.answer("Status refreshed!", show_alert=True)

        else:
            await query.answer("Invalid action.", show_alert=True)

    except Exception as e:
        print(f"Error handling callback query: {e}")
        await query.answer("An error occurred. Please try again later.", show_alert=True)
