# IMPORTS
import logging, asyncio, os, re, random, pytz, aiohttp, string
from datetime import datetime, timedelta
from config import SHORTLINK_API, SHORTLINK_URL, TOKENTIME
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TOKENS = {}
VERIFIED = {}

# GET SHORT LINK
async def get_verify_shorted_link(link):
    if SHORTLINK_URL == "api.shareus.io":
        url = f'https://{SHORTLINK_URL}/easy_api'
        params = {
            "key": SHORTLINK_API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)
        return await shortzy.convert(link)

# CREATE TOKEN LINK
async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))

    TOKENS[user.id] = {token: False}  # Token not used yet

    full_link = f"{link}verify-{user.id}-{token}"
    shortened = await get_verify_shorted_link(full_link)
    return str(shortened)

# CHECK TOKEN VALIDITY
async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if user.id in TOKENS:
        return token in TOKENS[user.id] and TOKENS[user.id][token] is False
    return False

# VERIFY USER AND SET 24h EXPIRY
async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    if user.id not in TOKENS or token not in TOKENS[user.id]:
        return

    TOKENS[user.id][token] = True
    expiry = datetime.now(pytz.utc) + timedelta(seconds=TOKENTIME)
    VERIFIED[user.id] = expiry.isoformat()  # Store expiry as string

# CHECK IF USER STILL VERIFIED
async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    if user.id in VERIFIED:
        expiry_time = datetime.fromisoformat(VERIFIED[user.id])
        return datetime.now(pytz.utc) <= expiry_time
    return False
