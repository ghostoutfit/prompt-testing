import streamlit as st
from datetime import datetime, date
import random
from PIL import Image

from google_sheets import (
    get_student_info,
    create_student_if_missing,
    add_goal_history_entry,
    update_student_current_goal,
    get_goal_history_for_student,
    get_sheet
)

from openai import OpenAI
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])




