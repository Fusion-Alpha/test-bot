import os
import json

# Storage
storage = {
    "file": "website_data.json",
    "websites": {},  # Will store WebsiteMonitor instances
    "repeat_interval": None,
    "latest_notification": {"message_id": None, "number": None, "flag_url": None, "site_id": None, "multiple": False, "is_first_run": False},
    "active_countdown_tasks": {}
}

async def load_website_data():
    """Load website data from file"""
    data = {}
    if os.path.exists(storage["file"]):
        try:
            with open(storage["file"], "r") as f:
                data = json.load(f)
                # print(f"[DEBUG] load_website_data - loaded data from file: {data}")

                # Load data for each website
                for site_id, website in storage["websites"].items():
                    if site_id in data:
                        # print(f"[DEBUG] load_website_data - loading data for {site_id}")
                        # Load last_number from the file for all website types
                        website.last_number = data[site_id].get("last_number")

                        # For multiple numbers website, also load latest_numbers
                        if website.type == "multiple":
                            latest_numbers = data[site_id].get("latest_numbers", [])
                            if latest_numbers:
                                website.latest_numbers = latest_numbers

                                # If last_number is not set, extract it from first element
                                if website.last_number is None and latest_numbers:
                                    first_num = latest_numbers[0]
                                    if isinstance(first_num, str) and first_num.startswith("+"):
                                        first_num = first_num[1:]
                                    try:
                                        website.last_number = int(first_num)
                                    except (ValueError, TypeError):
                                        website.last_number = None

                        # Load button_updated state if it exists
                        if "button_updated" in data[site_id]:
                            website.button_updated = data[site_id]["button_updated"]
                            # print(f"[DEBUG] load_website_data - loaded button_updated={website.button_updated} for {site_id}")
        except (json.JSONDecodeError, IOError) as e:
            # print(f"Error loading website data: {e}")
            pass
    return data

async def save_website_data(site_id=None):
    # Load existing data
    data = {}
    if os.path.exists(storage["file"]):
        try:
            with open(storage["file"], "r") as f:
                data = json.load(f)
                # print(f"[DEBUG] save_website_data - loaded existing data: {data}")
        except (json.JSONDecodeError, IOError) as e:
            # print(f"[DEBUG] save_website_data - error loading existing data: {e}")
            pass

    # Update data
    if site_id:
        # Update just one website
        if site_id in storage["websites"]:
            website = storage["websites"][site_id]
            # print(f"[DEBUG] website object for {site_id}: {website}")
            # print(f"[DEBUG] button_updated state: {getattr(website, 'button_updated', False)}")
            # if hasattr(website, 'latest_numbers'):
                # print(f"[DEBUG] latest_numbers for {site_id}: {website.latest_numbers}")
            # else:
                # print(f"[DEBUG] latest_numbers for {site_id}: None (attribute missing)")
            
            # For multiple numbers websites, save last_number and always include latest_numbers (empty if not set)
            if website.type == "multiple":
                data[site_id] = {
                    "last_number": website.last_number,
                    "latest_numbers": website.latest_numbers
                }
                # Ensure latest_numbers is always an array
                if data[site_id]["latest_numbers"] is None:
                    data[site_id]["latest_numbers"] = []
            else:
                # For all other websites, just save the last_number
                data[site_id] = {
                    "last_number": website.last_number
                }

    else:
        # Update all websites
        for site_id, website in storage["websites"].items():
            # print(f"[DEBUG] save_website_data - processing {site_id}")
            # if hasattr(website, 'latest_numbers'):
            #     print(f"[DEBUG] save_website_data - latest_numbers for {site_id}: {website.latest_numbers}")
            # else:
            #     print(f"[DEBUG] save_website_data - latest_numbers for {site_id}: None (attribute missing)")
            if website.type == "multiple":
                data[site_id] = {
                    "last_number": website.last_number,
                    "latest_numbers": website.latest_numbers
                }
                if data[site_id]["latest_numbers"] is None:
                    data[site_id]["latest_numbers"] = []
            else:
                data[site_id] = {
                    "last_number": website.last_number
                }

    # Save to file
    try:
        with open(storage["file"], "w") as f:
            json.dump(data, f)
            # print(f"[DEBUG] save_website_data - saved data to file: {data}")
    except IOError as e:
        # print(f"Error saving website data: {e}")
        pass

async def save_last_number(number, site_id):
    """Save last number for a specific website"""
    if site_id in storage["websites"]:
        website = storage["websites"][site_id]
        website.last_number = number
        await save_website_data(site_id)
