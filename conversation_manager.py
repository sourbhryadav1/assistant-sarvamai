import json
import os
import re
from datetime import datetime
from typing import Any, Tuple # type hinting

from chat import chat_with_sarvam
from translate import translate_text

DB_FILE = "db.json"

class ConversationManager:
    """
    Manages the state and flow of a structured conversation to gather user data,
    including input validation and normalization.
    """
    def __init__(self, flow_script_path="conversation_flow.json"):
        with open(flow_script_path, 'r') as f:
            self.script = json.load(f)
        
        self.user_language_code = 'en-IN' # Default language
        
        self.flow_order = [
            "askLanguage", "askName", "askPincode", "askCity", "askAge", "askGender",
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
        is_valid, normalized_value, error_message = self._validate_and_normalize(user_input, current_key)

        if not is_valid:
            return error_message

        # If valid, store the normalized data
        storage_key = current_key.replace("ask", "").lower()
        self.user_data[storage_key] = normalized_value

        if current_key == 'askLanguage':
            self.user_language_code = normalized_value

        self.current_step += 1

        if self.current_step >= len(self.flow_order):
            self.is_complete = True
            self._save_to_db()
            goodbye_message = self.script.get("goodbye", "Thank you!")
            return self._translate_if_needed(goodbye_message)
        
        next_key = self.flow_order[self.current_step]
        next_question = self.script[next_key]
        return self._translate_if_needed(next_question)
    
    def _translate_if_needed(self, text: str) -> str:
        """Helper function to translate text if user's language is not English."""
        if self.user_language_code != 'en-IN':
            return translate_text(text, self.user_language_code)
        return text
    
    def _get_llm_validation_prompt(self, key: str) -> str:
        """Returns the system prompt for a specific validation task."""
        if key == "askName":
            return """
            You are a data validation expert. Analyze the user's response to extract a person's full name.
            If a valid name is found, respond ONLY with `true: <Full Name>`.
            Example 1: User says 'my name is Vikram Singh'. Respond `true: Vikram Singh`.
            Example 2: User says 'xoxo'. Respond `true: Xoxo`.
            If no name can be extracted, or if the input is nonsensical, respond ONLY with `false: That does not sound like a valid name. Please tell me your full name.`.
            """
        if key in ["askAge", "askPincode", "askExperience", "askLastSalary", "askExpectedSalary"]:
            return """
            You are a data validation expert. Analyze the user's response to extract a single numerical value.
            Convert spoken numbers, digits, and Indian number formats (lakh, crore) into an integer.
            If a valid number is found, respond ONLY with `true: <integer>`.
            Example 1: User says 'pachas hazaar'. Respond `true: 50000`.
            If no valid number can be extracted, respond ONLY with `false: I did not understand that as a number. Please state the number clearly.`.
            """
        if key == "askCity":
            return """
            You are a data validation expert for an Indian job portal.
            Analyze the user's response to identify a single city name in India.
            If a valid Indian city name is found, respond ONLY with `true: <City Name>`.
            If no valid city name can be extracted, respond ONLY with `false: That does not seem to be a valid city in India. Please tell me your current city.`.
            """
        if key == "askRole":
            return f"""
            You are a data validation expert for a job portal in India.
            Analyze the user's stated job role. Normalize it to a standard job title.
            If the input is a valid job, respond ONLY with `true: <Standard Job Title>`.
            If the input is not a valid job role, respond ONLY with `false: I did not recognize that as a job role. Please tell me the type of job you are looking for.`.
            """
        if key == "askEducation":
            return """
            You are a data validation expert. Analyze the user's education level.
            Normalize it to one of: 10th Pass, 12th Pass, Graduate, Post Graduate, Other.
            If valid, respond ONLY with `true: <Normalized Level>`.
            If invalid or unclear, respond ONLY with `false: Please state a valid education level, like 12th pass or graduate.`.
            """
        if key == "askTravelDistance":
            return """
            You are a data validation expert. Analyze the user's travel distance preference.
            Extract and normalize the distance.
            If valid, respond ONLY with `true: <Normalized Distance>`.
            If invalid or unclear, respond ONLY with `false: I did not understand the distance. Please tell me how far you are willing to travel, for example, 10 to 20 kilometers.`.
            """
        return ""

    def _validate_and_normalize(self, text: str, key: str) -> Tuple[bool, Any, str | None]:
        """
        Validates input using rules for simple types and LLM for complex types.
        """

        # --- RULE-BASED VALIDATION for Language Selection ---
        if key == "askLanguage":
            text_lower = text.lower()
            lang_map = {
                'en-IN': ['english', 'angrezi'],
                'hi-IN': ['hindi'],
                'bn-IN': ['bengali', 'bangla'],
                'gu-IN': ['gujarati'],
                'kn-IN': ['kannada'],
                'ml-IN': ['malayalam'],
                'mr-IN': ['marathi'],
                'od-IN': ['odia', 'oriya'],
                'pa-IN': ['punjabi'],
                'ta-IN': ['tamil', 'tamizh'],
                'te-IN': ['telugu'],
                'as-IN': ['assamese', 'asomiya'],
                'brx-IN': ['bodo'],
                'doi-IN': ['dogri'],
                'kok-IN': ['konkani'],
                'ks-IN': ['kashmiri'],
                'mai-IN': ['maithili'],
                'mni-IN': ['manipuri', 'meiteilon'],
                'ne-IN': ['nepali'],
                'sa-IN': ['sanskrit'],
                'sat-IN': ['santali'],
                'sd-IN': ['sindhi'],
                'ur-IN': ['urdu']
            }
            for code, keywords in lang_map.items():
                if any(keyword in text_lower for keyword in keywords):
                    return (True, code, None)
            return (False, None, self.script.get("repromptLanguage"))
        
        # --- LLM VALIDATION FOR ALL COMPLEX AND NUMERIC FIELDS ---
        if key in ["askName", "askRole", "askEducation", "askTravelDistance", "askAge", "askPincode", "askExperience", "askLastSalary", "askExpectedSalary", "askCity"]:
            system_prompt = self._get_llm_validation_prompt(key)
            message = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            print(f"[INFO] Using LLM to validate '{key}' for input: '{text}'...")
            response = chat_with_sarvam(message)
            
            if response and ':' in response:
                parts = response.split(':', 1)
                status = parts[0].strip().lower()
                value_str = parts[1].strip()
                
                if status == 'true':
                    value = None
                    # For numeric fields, try to cast to int
                    if "Pincode" in key or "Age" in key or "Salary" in key or "Experience" in key:
                        try:
                            value = int(value_str)
                        except ValueError:
                             pass
                    else:
                        value = value_str # For other fields, keep as string

                    if value is not None:
                        # --- SECONDARY RULE-BASED CHECKS on LLM output ---
                        if key == "askAge" and not (18 <= value <= 80):
                            return (False, None, self._translate_if_needed(self.script.get("repromptAge")))
                        if key == "askPincode" and len(str(value)) != 6:
                            return (False, None, self.__translate_if_needed(self.script.get("repromptPincode")))
                        return (True, value, None) 
                else:
                    return (False, None, self._translate_if_needed(value_str)) # use llm response as reprompt message

            # If LLM fails, returns false, or value is None, use the specific reprompt key
            reprompt_key = f"reprompt{key.replace('ask', '')}"
            return (False, None, self._translate_if_needed(self.script.get(reprompt_key, "Please try again.")))

        # --- RULE-BASED VALIDATION FOR SIMPLEST FIELDS ---
        text_cleaned = text.lower().strip().rstrip('.')
        
        if key == "askGender":
            if any(word in text_cleaned for word in ["mail", "male"]): return (True, "Male", None)
            if "female" in text_cleaned: return (True, "Female", None)
            if "other" in text_cleaned: return (True, "Other", None)
            return (False, None, self._translate_if_needed(self.script.get("repromptGender")))
            
        # For Name and City
        return (True, text_cleaned.title(), None)
    
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

