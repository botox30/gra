
import json
import datetime
import os
from typing import Dict, Optional, Tuple

class ManualSubscriptionManager:
    def __init__(self, file_path: str = "subscriptions.json"):
        # Make sure we use the correct path relative to the ReceiptGenBot directory
        if not file_path.startswith("/") and not os.path.dirname(file_path):
            # If it's just a filename, put it in the ReceiptGenBot directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)  # Go up from receiptgen to ReceiptGenBot
            self.file_path = os.path.join(project_root, file_path)
        else:
            self.file_path = file_path
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Create the subscriptions file if it doesn't exist"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f, indent=2)
    
    def load_subscriptions(self) -> Dict:
        """Load subscriptions from JSON file"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_subscriptions(self, subscriptions: Dict):
        """Save subscriptions to JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(subscriptions, f, indent=2)
    
    def add_subscription(self, user_id: int, days: int = None, guild_id: int = None):
        """Add or update a subscription manually"""
        subscriptions = self.load_subscriptions()
        user_key = str(user_id)
        
        if days:
            # Calculate end date
            end_date = datetime.datetime.now() + datetime.timedelta(days=days)
            end_date_str = end_date.isoformat()
            is_forever = False
        else:
            # Forever subscription
            end_date_str = None
            is_forever = True
        
        subscriptions[user_key] = {
            "user_id": user_id,
            "guild_id": guild_id,
            "days": days,
            "is_forever": is_forever,
            "end_date": end_date_str,
            "is_active": True,
            "created_at": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        self.save_subscriptions(subscriptions)
        return subscriptions[user_key]
    
    def get_subscription(self, user_id: int) -> Optional[Dict]:
        """Get subscription info for a user"""
        subscriptions = self.load_subscriptions()
        user_key = str(user_id)
        
        if user_key not in subscriptions:
            return None
        
        sub = subscriptions[user_key]
        
        # Check if subscription is still active
        if sub.get("end_date") and not sub.get("is_forever", False):
            end_date = datetime.datetime.fromisoformat(sub["end_date"])
            if datetime.datetime.now() > end_date:
                sub["is_active"] = False
                subscriptions[user_key] = sub
                self.save_subscriptions(subscriptions)
        
        return sub
    
    def remove_subscription(self, user_id: int) -> bool:
        """Remove a subscription"""
        subscriptions = self.load_subscriptions()
        user_key = str(user_id)
        
        if user_key in subscriptions:
            del subscriptions[user_key]
            self.save_subscriptions(subscriptions)
            return True
        return False
    
    def get_active_subscriptions(self) -> Dict:
        """Get all active subscriptions"""
        subscriptions = self.load_subscriptions()
        active = {}
        
        for user_id, sub in subscriptions.items():
            # Update active status
            if sub.get("end_date") and not sub.get("is_forever", False):
                end_date = datetime.datetime.fromisoformat(sub["end_date"])
                sub["is_active"] = datetime.datetime.now() <= end_date
            
            if sub.get("is_active", False):
                active[user_id] = sub
        
        # Save updated active statuses
        self.save_subscriptions(subscriptions)
        return active
    
    def get_subscription_display_info(self, user_id: int) -> Tuple[str, str, bool]:
        """Get display info for subscription (till_text, ends_text, is_active)"""
        sub = self.get_subscription(user_id)
        
        if not sub:
            return "`None`", "`None`", False
        
        if sub.get("is_forever", False):
            return "`Forever`", "`Never`", True
        
        if sub.get("end_date"):
            end_date = datetime.datetime.fromisoformat(sub["end_date"])
            timestamp = int(end_date.timestamp())
            
            if sub.get("is_active", False):
                till_text = f"<t:{timestamp}:D>"
                ends_text = f"<t:{timestamp}:R>"
            else:
                till_text = "`Expired`"
                ends_text = f"<t:{timestamp}:R>"
            
            return till_text, ends_text, sub.get("is_active", False)
        
        return "`None`", "`None`", False
