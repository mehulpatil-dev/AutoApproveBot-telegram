from pymongo import MongoClient
from config import MONGO

client = MongoClient(MONGO)

users = client['main']['users']
groups = client['main']['groups']
check_time = client['main']['timer']

def already_db(user_id):
        user = users.find_one({"user_id" : str(user_id)})
        if not user:
            return False
        return True

def already_dbg(chat_id):
        group = groups.find_one({"chat_id" : str(chat_id)})
        if not group:
            return False
        return True
        
def add_user(user_id):
    in_db = already_db(user_id)
    if in_db:
        return
    return users.insert_one({"user_id": str(user_id)}) 

def remove_user(user_id):
    in_db = already_db(user_id)
    if not in_db:
        return 
    return users.delete_one({"user_id": str(user_id)})
    
def add_group(chat_id):
    in_db = already_dbg(chat_id)
    if in_db:
        return
    return groups.insert_one({"chat_id": str(chat_id)})

def all_users():
    user = users.find({})
    usrs = len(list(user))
    return usrs

def all_groups():
    group = groups.find({})
    grps = len(list(group))
    return grps

from pymongo import MongoClient
from config import MONGO

client = MongoClient(MONGO)
check_time = client['main']['timer']


def update_time(status=None, time=None):
    # Load or initialize the timer document
        try:
            timer = check_time.find_one({"_id": "timer"})
            
            if not timer:
                timer = {"_id": "timer", "status": "off", "time": 0}
                check_time.insert_one(timer)
        
            update_data = {}
        
            # Update status if provided ("on" or "off")
            if status is not None:
                update_data["status"] = str(status).lower()
        
            # Update time if provided
            if time is not None:
                update_data["time"] = int(time)
        
            # Apply updates if any
            if update_data:
                check_time.update_one({"_id": "timer"}, {"$set": update_data})
                timer.update(update_data)  # update local copy
        except Exception as e:
                return False,e
        return True


# ------- GETTER FUNCTIONS -------- #

def get_time():
    timer = check_time.find_one({"_id": "timer"})
    return timer["time"] if timer else 0


def get_status():
    timer = check_time.find_one({"_id": "timer"})
    return timer["status"] if timer else "off"


def get_all():
    timer = check_time.find_one({"_id": "timer"})
    return timer if timer else {"status": "off", "time": 0}

# ============ APPEND THIS BLOCK TO THE END OF database.py ============
# (uses the same `client` already created at the top of database.py)

from datetime import datetime, timedelta

channel_stats = client['main']['channel_stats']


def track_channel_join(chat_id, chat_title, user_id):
    """Call this once per successful approval to log it for stats."""
    channel_stats.insert_one({
        "chat_id": str(chat_id),
        "chat_title": chat_title,
        "user_id": str(user_id),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "timestamp": datetime.utcnow(),
    })


def get_all_tracked_channels():
    """Returns [{chat_id, chat_title, total_joins}, ...] for every channel seen so far."""
    chat_ids = channel_stats.distinct("chat_id")
    channels = []
    for cid in chat_ids:
        total = channel_stats.count_documents({"chat_id": cid})
        latest = list(channel_stats.find({"chat_id": cid}).sort("timestamp", -1).limit(1))
        title = latest[0]["chat_title"] if latest else "Unknown Channel"
        channels.append({"chat_id": cid, "chat_title": title, "total_joins": total})
    return channels


def get_channel_stats(chat_id, days=7):
    """Returns total + a day-by-day breakdown for the last `days` days, or None if unseen."""
    chat_id = str(chat_id)
    total_joins = channel_stats.count_documents({"chat_id": chat_id})
    if total_joins == 0:
        return None

    latest = list(channel_stats.find({"chat_id": chat_id}).sort("timestamp", -1).limit(1))
    chat_title = latest[0]["chat_title"] if latest else "Unknown Channel"

    today = datetime.utcnow().date()
    daily_breakdown = []
    period_total = 0
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        count = channel_stats.count_documents({"chat_id": chat_id, "date": day_str})
        period_total += count
        daily_breakdown.append({"date": day_str, "day_name": day.strftime("%A"), "count": count})

    return {
        "chat_id": chat_id,
        "chat_title": chat_title,
        "total_joins": total_joins,
        "period_total": period_total,
        "daily_breakdown": daily_breakdown,
    }
