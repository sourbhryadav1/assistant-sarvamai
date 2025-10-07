import os
from flask import Flask, request, Response
import dotenv
from conversation_manager import ConversationManager

dotenv.load_dotenv()