import json
import os
import re
from datetime import datetime
from typing import Any, Tuple # type hinting

DB_FILE = "db.json"

class ConversationManager:
    """
    Manages the state and flow of a structured conversation to gather user data,
    including input validation and normalization.
    """
    def __init__(self, flow_script_path="conversation_flow.json"):
        with open(flow_script_path, 'r') as f:
            self.script = json.load(f)
        
        self.flow_order = [
            "askName", "askPincode", "askCity", "askAge", "askGender",
            "askEducation", "askExperience", "askLastSalary",
            "askExpectedSalary", "askTravelDistance", "askRole"
        ]
        
        self.user_data = {}
        self.current_step = 0
        self.is_complete = False
        print("[INFO] ConversationManager initialized with validation logic.")

    def start_conversation(self) -> str:
        welcome_message = self.script.get("welcome", "Welcome!")
        first_question = self.script[self.flow_order[0]]
        return f"{welcome_message} {first_question}"

    def process_user_response(self, user_input: str) -> str:
        """
        Validates and saves the user's response, then returns the next question or a re-prompt.
        """
        if self.is_complete:
            return self.script.get("goodbye", "Thank you!")

        current_key = self.flow_order[self.current_step]
        is_valid, normalized_value, error_key = self._validate_and_normalize(user_input, current_key)

        if not is_valid:
            # If input is invalid, return the specific re-prompt message and do not advance.
            return self.script.get(error_key, "Please try again.")

        # If valid, store the normalized data
        storage_key = current_key.replace("ask", "").lower()
        self.user_data[storage_key] = normalized_value
        self.current_step += 1

        if self.current_step >= len(self.flow_order):
            self.is_complete = True
            self._save_to_db()
            return self.script.get("goodbye", "Thank you!")
        
        next_key = self.flow_order[self.current_step]
        return self.script[next_key]

    def _validate_and_normalize(self, text: str, key: str) -> Tuple[bool, Any, str]:
        """
        Validates input based on the question key.
        Returns (isValid, normalizedValue, repromptKey).
        """
        text = text.lower().strip().rstrip('.')

        if key in ["askAge", "askExperience", "askLastSalary", "askExpectedSalary"]:
            number = self._text_to_int(text)
            if number is None:
                return (False, None, "repromptNumber")
            
            # --- ADDED EXPERIENCE VALIDATION ---
            if key == "askExperience" and not (0 <= number <= 50):
                return (False, None, "repromptExperience")
            
            # --- ADDED AGE VALIDATION ---
            if key == "askAge":
                if not (18 <= number <= 80): # Assuming a reasonable age range for job seekers
                    return (False, None, "repromptAge")
            # ---------------------------
            return (True, number, None)

        if key == "askPincode":
            number = self._text_to_int(text)
            if number is None or len(str(number)) != 6:
                return (False, None, "repromptPincode")
            return (True, number, None)
            
        if key == "askGender":
            if any(word in text for word in ["mail", "male"]):
                return (True, "Male", None)
            if any(word in text for word in ["female"]):
                return (True, "Female", None)
            if any(word in text for word in ["other"]):
                return (True, "Other", None)
            return (False, None, "repromptGender")
        
        if key == "askEducation":
            education_levels = {"10th pass": ["10th", "tenth"], "12th pass": ["12th", "twelfth"], "graduate": ["graduate", "degree"], "post graduate": ["post graduate", "masters"], "other": ["other"]}
            for level, keywords in education_levels.items():
                if any(keyword in text for keyword in keywords):
                    return (True, level.title(), None)
            return (False, None, "repromptEducation")

        if key == "askTravelDistance":
            match = re.search(r'(\d+)\s*(to|-)\s*(\d+)', text)
            if match:
                return (True, f"{match.group(1)}-{match.group(3)} km", None)
            
            # Check for "more than"
            match_more = re.search(r'(more than|over|greater than)\s*(\d+)', text)
            if match_more:
                return (True, f"More than {match_more.group(2)} km", None)
            
            match_less = re.search(r'(less than|under|below)\s*(\d+)', text)
            if match_less:
                return (True, f"Less than {match_less.group(2)} km", None)
                
            return (False, None, "repromptTravel")

        if key == "askRole":
            roles = ["plumber", "driver", "packer", "mover", "mason", "cook", "cleaner", "painter", "line worker", "clerk", "construction", "welder", "electrician", "security", "guard", "barber", "rider", "delivery"]
            for role in roles:
                if role in text:
                    # Normalize common variations
                    if role in ["packer", "mover"]: return (True, "Packers & Movers", None)
                    if role in ["security", "guard"]: return (True, "Security Guard", None)
                    if role in ["rider", "delivery"]: return (True, "Rider (Delivery)", None)
                    if role == "construction": return (True, "Construction Worker", None)
                    return (True, role.title(), None)
            return (False, None, "repromptRole")

        # For simple text fields, just clean and capitalize
        return (True, text.title(), None)

    def _text_to_int(self, text: str) -> int | None:
        """Converts spoken numbers and digits into an integer."""
        text = text.lower().replace(',', '').strip()
        
        # Direct conversion if it's already a number
        if text.isdigit():
            return int(text)

        # Handle simple number words
        num_words = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        if text in num_words:
            return num_words[text]
        
        # Handle cases like "five six triple zero one" -> 560001
        try:
            cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
            words = cleaned_text.split()
            digits = [str(num_words.get(word, word)) for word in words]
            # Handle 'triple' keyword common in India for numbers
            final_digits = []
            i = 0
            while i < len(digits):
                if digits[i] == 'triple' and i + 1 < len(digits):
                    final_digits.extend([digits[i+1]] * 3)
                    i += 2
                else:
                    final_digits.append(digits[i])
                    i += 1
            
            num_str = "".join(digit for digit in final_digits if digit.isdigit())
            if num_str:
                return int(num_str)
        except Exception:
            pass # Fallback

        # Handle thousands, lakhs, crores
        multipliers = {'thousand': 1000, 'lakh': 100000, 'crore': 10000000}
        parts = text.split()
        if len(parts) == 2 and parts[1] in multipliers:
            try:
                num = float(parts[0]) if '.' in parts[0] else int(parts[0])
                return int(num * multipliers[parts[1]])
            except (ValueError, IndexError):
                return None

        return None

    def _save_to_db(self):
        print(f"[INFO] Saving user data to {DB_FILE}...")
        self.user_data["submission_timestamp"] = datetime.now().isoformat()
        all_users = []
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    all_users = json.load(f)
                if not isinstance(all_users, list):
                    all_users = []
            except json.JSONDecodeError:
                all_users = []
        
        all_users.append(self.user_data)
        with open(DB_FILE, 'w') as f:
            json.dump(all_users, f, indent=4)
        print("[INFO] Data saved successfully.")

