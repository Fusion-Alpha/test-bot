import os, asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.storage import storage
from bot.config import CHAT_ID, ENABLE_REPEAT_NOTIFICATION
from bot.utils import get_base_url, format_phone_number

def create_unified_keyboard(data, website=None):
    """
    Create a unified keyboard layout based on website type and state
    
    Parameters:
    - data: Dictionary containing:
        - site_id: The site ID
        - updated: Boolean indicating if the numbers were just updated
        - type: 'single' or 'multiple'
        - is_initial_run: Boolean for multiple type sites
        - number: For single type sites
        - numbers: List of numbers for multiple type sites
        - url: Website URL
    - website: Website object (optional, used for fallback)
    
    Returns:
    - InlineKeyboardMarkup with appropriate buttons
    """
    site_id = data.get("site_id")
    updated = data.get("updated", False)
    website_type = data.get("type")
    is_initial_run = data.get("is_initial_run", False)
    url = data.get("url", "")
    
    # If website object is provided, use it for fallback values and prioritize its attributes
    if website:
        # Get button_updated state from website object
        button_updated = getattr(website, 'button_updated', False)
        # print(f"[DEBUG] create_unified_keyboard - website object provided with button_updated: {button_updated}")
        
        # Prioritize the website object's button_updated state over the passed updated parameter
        if button_updated:
            updated = True
            # print(f"[DEBUG] create_unified_keyboard - using website's button_updated state: {updated}")
        
        # Prioritize the website's type over the passed type
        if hasattr(website, "type") and website.type:
            if website_type != website.type:
                # print(f"[DEBUG] create_unified_keyboard - overriding type from {website_type} to {website.type}")
                website_type = website.type
        
        if not website_type and hasattr(website, "type"):
            website_type = website.type
            
        if not url and hasattr(website, "url"):
            url = website.url
    
    # print(f"[DEBUG] create_unified_keyboard - site_id: {site_id}, updated: {updated}, type: {website_type}")
    
    # Ensure we have a valid URL
    if not url:
        url = get_base_url() or ""
    
    # Create buttons based on website type
    if website_type == "single":
        number = data.get("number", "")
        if not number and website and hasattr(website, "last_number"):
            number = website.last_number
        
        # Format the number with proper country code spacing
        formatted_number = format_phone_number(number)
        
        # Update button text based on state
        update_text = "✅ Updated Number" if updated else "🔄 Update Number"
        # print(f"[DEBUG] create_unified_keyboard - single type update_text: {update_text}")
        
        # Create the keyboard for single type
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📋 Copy Number", callback_data="copy_number"),
                    InlineKeyboardButton(text=update_text, callback_data=f"update_{number}_{site_id}")
                ],
                [
                    InlineKeyboardButton(text="🔪 Split", callback_data=f"split_{number}"),
                    InlineKeyboardButton(text="⚙️ Settings", callback_data=f"settings_{site_id}")
                ],
                [
                    InlineKeyboardButton(text="🌐 Visit Webpage", url=f"{url}/number/{number}" if number else url)
                ]
            ]
        )
    else:  # Multiple type
        numbers = data.get("numbers", [])
        if not numbers and website:
            if hasattr(website, "latest_numbers") and website.latest_numbers:
                numbers = website.latest_numbers
            elif hasattr(website, "last_number") and website.last_number:
                numbers = [website.last_number]
        
        # Update button text based on state
        update_text = "✅ Updated Numbers" if updated else "🔄 Update Numbers"
        # print(f"[DEBUG] create_unified_keyboard - multiple type update_text: {update_text}")
        
        # For initial run with a single number, create a consistent layout
        if is_initial_run and (not numbers or len(numbers) <= 1):
            # Get the number to display and format it
            raw_number = numbers[0] if numbers else ""
            display_number = format_phone_number(raw_number)
            
            # Create a layout with the number in the first row
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=display_number, callback_data=f"number_{raw_number}_{site_id}")
                    ],
                    [
                        InlineKeyboardButton(text=update_text, callback_data=f"update_multi_{site_id}"),
                        InlineKeyboardButton(text="⚙️ Settings", callback_data=f"settings_{site_id}")
                    ],
                    [
                        InlineKeyboardButton(text="🌐 Visit Webpage", url=url)
                    ]
                ]
            )
        # For non-initial run or multiple numbers, create the standard layout
        else:
            # Create buttons for each number with maximum 2 buttons per row
            buttons = []
            current_row = []
            
            for i, raw_number in enumerate(numbers):
                # Format the number with proper country code spacing
                formatted_number = format_phone_number(raw_number)
                
                # Add button to current row
                current_row.append(InlineKeyboardButton(text=formatted_number, callback_data=f"number_{raw_number}_{site_id}"))
                
                # If we have 2 buttons in the current row, add it to buttons and start a new row
                if len(current_row) == 2:
                    buttons.append(current_row)
                    current_row = []
            
            # Add any remaining buttons in the last row if it's not empty
            if current_row:
                buttons.append(current_row)
            
            # Add control buttons
            buttons.append([
                InlineKeyboardButton(text=update_text, callback_data=f"update_multi_{site_id}"),
                InlineKeyboardButton(text="⚙️ Settings", callback_data=f"settings_{site_id}")
            ])
            
            # Add the Visit Webpage button as a new row at the end
            buttons.append([InlineKeyboardButton(text="🌐 Visit Webpage", url=url)])
            
            # Create the keyboard with the buttons
            return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_buttons(number, updated=False, site_id=None):
    """Legacy function for backward compatibility"""
    website = storage["websites"].get(site_id)
    if not website:
        return None

    data = {
        "type": "single",
        "number": number,
        "site_id": site_id,
        "updated": updated,
        "url": getattr(website, 'url', get_base_url() or "")
    }

    return create_unified_keyboard(data, website)

def get_multiple_buttons(numbers, site_id=None):
    """Legacy function for backward compatibility"""
    website = storage["websites"].get(site_id)
    if not website:
        return None

    data = {
        "type": "multiple",
        "numbers": numbers,
        "site_id": site_id,
        "updated": False,  # Default to not updated
        "url": getattr(website, 'url', get_base_url() or ""),
        "is_initial_run": getattr(website, 'first_run', False)
    }

    # Try to determine if this is an initial run if the attribute is not present
    if not hasattr(website, 'first_run'):
        if (not hasattr(website, 'latest_numbers') or 
            not website.latest_numbers or 
            len(website.latest_numbers) == 0):
            data["is_initial_run"] = True

    return create_unified_keyboard(data, website)

async def send_notification(bot, data):
    try:
        chat_id = os.getenv("CHAT_ID")
        # print(f"[DEBUG] send_notification - chat_id: {chat_id}")
        # print(f"[DEBUG] send_notification - data: {data}")
        
        if not chat_id:
            return

        site_id = data.get("site_id")
        website = storage["websites"].get(site_id)

        if not website:
            # print(f"[ERROR] send_notification - website not found for site_id: {site_id}")
            return

        # Determine if this is a single or multiple number notification based on website type
        is_multiple = website.type == "multiple"
        flag_url = data.get("flag_url")

        if not is_multiple:
            # Single number notification
            number = data.get("number")

            if not number or not flag_url:
                # print(f"[ERROR] send_notification - missing number or flag_url for site_id: {site_id}")
                return

            message = f"🎁 *New Number Added* 🎁\n\n`{number}` check it out! 💖"
            keyboard = get_buttons(number, site_id=site_id)

            try:
                sent_message = await bot.send_photo(
                    chat_id,
                    photo=flag_url,
                    caption=message,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                # print(f"[DEBUG] send_notification - sent message to {chat_id}")
            except Exception as e:
                # print(f"[ERROR] send_notification - failed to send message to {chat_id}: {e}")
                return

            # Store notification data
            storage["latest_notification"] = {
                "message_id": sent_message.message_id,
                "number": number,
                "flag_url": flag_url,
                "site_id": site_id,
                "multiple": False,
                "is_first_run": False
            }

            # Handle repeat notification if enabled
            if ENABLE_REPEAT_NOTIFICATION and storage["repeat_interval"] is not None:
                await add_countdown_to_latest_notification(bot, storage["repeat_interval"], site_id)

        else:
            # Multiple numbers notification
            numbers = data.get("numbers", [])

            if not numbers:
                # print(f"[ERROR] send_notification - missing numbers for site_id: {site_id}")
                return

            # Check if this is the first run 
            is_first_run = (not website.latest_numbers) or (
                any(num == f"+{website.last_number}" for num in website.latest_numbers) and len(website.latest_numbers) == len(numbers)
            )

            if is_first_run or len(numbers) == 1:
                # On first run or single number, send notification with the last_number
                notification_message = f"🎁 *New Numbers Added* 🎁\n\n`+{website.last_number}` check it out! 💖"

                # Create data for keyboard with single number
                keyboard_data = {
                    "type": "multiple",
                    "numbers": [f"+{website.last_number}"],
                    "site_id": site_id,
                    "updated": False,
                    "url": website.url,
                    "is_initial_run": True
                }
                
                keyboard = create_unified_keyboard(keyboard_data, website)
            else:
                notification_message = f"🎁 *New Numbers Added* 🎁\n\nFound `{len(numbers)}` numbers, check them out! 💖"
                
                # Create data for keyboard with all numbers
                keyboard_data = {
                    "type": "multiple",
                    "numbers": numbers,
                    "site_id": site_id,
                    "updated": False,
                    "url": website.url,
                    "is_initial_run": False
                }
                
                keyboard = create_unified_keyboard(keyboard_data, website)

            try:
                if flag_url:
                    sent_message = await bot.send_photo(
                        chat_id,
                        photo=flag_url,
                        caption=notification_message,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                else:
                    sent_message = await bot.send_message(
                        chat_id,
                        text=notification_message,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                # print(f"[DEBUG] send_notification - sent message to {chat_id}")
            except Exception as e:
                # print(f"[ERROR] send_notification - failed to send message to {chat_id}: {e}")
                return

            # Store notification data
            storage["latest_notification"] = {
                "message_id": sent_message.message_id,
                "numbers": numbers,
                "flag_url": flag_url,
                "site_id": site_id,
                "multiple": True,
                "is_first_run": is_first_run
            }

            # Handle repeat notification if enabled
            if ENABLE_REPEAT_NOTIFICATION and storage["repeat_interval"] is not None:
                await add_countdown_to_latest_notification(bot, storage["repeat_interval"], site_id)
    except Exception as e:
        # print(f"[ERROR] send_notification - unexpected error: {e}")
        pass

async def update_message_with_countdown(bot, message_id, number_or_numbers, flag_url, site_id):
    """
    Update the notification message with a countdown for the given site_id (works for both single and multiple numbers)
    """
    interval = storage["repeat_interval"]
    if interval is None:
        return

    website = storage["websites"].get(site_id)
    if not website:
        return

    # Determine if this is a multiple or single type site
    is_multiple = website.type == "multiple"
    last_update_time = time.time()
    current_message = None
    countdown_active = True

    while countdown_active:
        try:
            current_time = time.time()
            time_left = int(interval - (current_time - last_update_time))
            if time_left < 0:
                time_left = 0
            formatted_time = format_time(time_left)

            if is_multiple:
                # Multiple numbers message
                numbers = number_or_numbers if isinstance(number_or_numbers, list) else website.latest_numbers
                notification_message = f"🎁 *New Numbers Added* 🎁\n\nFound `{len(numbers)}` numbers, check them out! 💖\n\n⏱ Next notification in: *{formatted_time}*"
                keyboard = get_multiple_buttons(numbers, site_id=site_id)
            else:
                # Single number message
                number = number_or_numbers if isinstance(number_or_numbers, str) else website.last_number
                notification_message = f"🎁 *New Number Added* 🎁\n\n`{number}` check it out! 💖\n\n⏱ Next notification in: *{formatted_time}*"
                keyboard = get_buttons(number, site_id=site_id)

            await bot.edit_message_caption(
                chat_id=CHAT_ID,
                message_id=message_id,
                caption=notification_message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

            await asyncio.sleep(1)
            # Check if repeat_interval changed or task cancelled
            if storage["repeat_interval"] != interval or not storage["active_countdown_tasks"].get(site_id):
                countdown_active = False
        except Exception as e:
            # print(f"[ERROR] update_message_with_countdown - error: {e}")
            countdown_active = False

async def add_countdown_to_latest_notification(bot, interval_seconds, site_id):
    try:
        latest = storage["latest_notification"]
        if latest["message_id"] and latest["site_id"] == site_id:
            message_id = latest["message_id"]
            flag_url = latest.get("flag_url")
            if latest.get("multiple"):
                number_or_numbers = latest.get("numbers")
            else:
                number_or_numbers = latest.get("number")
            # Cancel any previous countdown for this site
            if site_id in storage["active_countdown_tasks"]:
                storage["active_countdown_tasks"][site_id].cancel()
            countdown_task = asyncio.create_task(
                update_message_with_countdown(bot, message_id, number_or_numbers, flag_url, site_id)
            )
            storage["active_countdown_tasks"][site_id] = countdown_task

    except Exception as e:
        # print(f"[ERROR] add_countdown_to_latest_notification - error: {e}")
        pass

async def repeat_notification(bot):
    """Send a repeat notification if enabled"""
    try:
        # Check if we have an active notification
        if "latest_notification" in storage and storage["latest_notification"]:
            # Get the notification details
            message_id = storage["latest_notification"].get("message_id")
            site_id = storage["latest_notification"].get("site_id", "site_1")
            multiple = storage["latest_notification"].get("multiple", False)

            # Update the message with the new countdown
            await add_countdown_to_latest_notification(bot, storage["repeat_interval"], site_id)
    
    except Exception as e:
        # print(f"[ERROR] repeat_notification - error: {e}")
        pass
