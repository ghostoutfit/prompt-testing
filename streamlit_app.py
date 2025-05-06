import streamlit as st
from openai import OpenAI
from google_sheets import get_sheet
from datetime import datetime
import time

# Set up OpenAI client
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Select the PromptTesting sheet
sheet = get_sheet("PromptTesting")
data = sheet.get_all_values()

# Define column indexes
HEADERS = data[0]
rows = data[1:]

IV_COL = 0  # Column A: Prompt
STUDENT_INPUT_COLS = [1, 2, 3]  # Columns B, C, D
AI_OUTPUT_COLS = [4, 5, 6]  # Columns E, F, G

# Display UI
st.title("Prompt Tester - Motivation Onboard")
st.write("This tool loops through prompts in Column A and runs standardized student inputs from Columns B–D through OpenAI.")

# Confirmation button
if st.button("Run Prompt Tests"):
    for i, row in enumerate(rows):
        row_number = i + 2  # account for header row
        prompt = row[IV_COL].strip()

        if not prompt:
            continue  # skip empty rows

        ai_responses = []

        for j, student_col in enumerate(STUDENT_INPUT_COLS):
            student_input = row[student_col].strip()

            messages = [
                {"role": "system", "content": "You are a chatbot responding to a 9th grade student in a relaxed, neutral tone."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": ""},
                {"role": "user", "content": student_input}
            ]

            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                reply = f"[Error: {e}]"

            ai_responses.append(reply)
            time.sleep(1)

        # Write the responses to the sheet
        for j, reply in enumerate(ai_responses):
            sheet.update_cell(row_number, AI_OUTPUT_COLS[j] + 1, reply)

    st.success("All prompts processed and responses written.")





