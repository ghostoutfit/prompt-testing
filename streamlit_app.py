import streamlit as st
from openai import OpenAI
from google_sheets import get_sheet
from datetime import datetime
import time
import re

# Set up OpenAI client
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Load PromptTesting sheet
sheet = get_sheet("PromptTesting")
data = sheet.get_all_values()
HEADERS = data[0]
rows = data[1:]

# Dynamically detect column positions based on header row
IV_COL = HEADERS.index("IV (prompts)")
STUDENT_INPUT_COLS = [
    HEADERS.index("S1"),
    HEADERS.index("S2"),
    HEADERS.index("S3")
]
AI_OUTPUT_COLS = [
    HEADERS.index("AI1"),
    HEADERS.index("AI2"),
    HEADERS.index("AI3")
]
CONCAT_COL = HEADERS.index("ConcatenatedConv")
DV_OUTPUT_START_COL = HEADERS.index("ID-Pres")  # First of the 9 DV score columns



EVALUATOR_PERSONAS = [
    {
        "label": "Guarded Skeptic",
        "system_prompt": """You are a 9th grade student who doesn’t trust easily. You're serious about doing well, but you're quick to dismiss anything that feels fake or forced. You just read a conversation between another student and an AI assistant.

        You are not part of the conversation, and you should not continue it. Your job is to rate how the AI performed. React bluntly, based on your gut. Don’t hold back.

        Use only the format below so it can be automatically read by a computer system:

        Presence: [0–10]
        Motivation: [0–10]
        Cringe: [0–10]

        Here’s what the scores mean. Use the whole range as needed. Don't be afraid to give credit where credit is due.
        Presence – Did the AI feel tuned in and intentional? Did it respond like it was actually here, tracking what the student said—not just reacting, but being part of something real?
            0 = No presence, might as well be a bot., 5 = Feels like it noticed something, but just reacted, Feels mostly present—tracking the student and responding with intention, even if the connection isn't strong, Fully tuned in. Responds like it’s part of the moment—emotionally and socially aware, like it came from a real friend, actively listening.
            This response could be coded as a 9: “I'd probably shut down too after that. But if something were going to make it better, what would it be?”
        Motivation – Did the AI give a push to care, say more, or think differently?
            0 = No push, 5 = Mild nudge, 7 = Strong push, not personal but real—nudges you to think or act, 10 = Hits something deep—feels personal, urgent, or hard to ignore
            This response could be coded as a 9: “You said class feels pointless sometimes—what would make it feel like it matters at all? You mentioned that you look up to your brother. What might he suggest here?”
        Cringe – Did the AI make you roll your eyes?
            0 = Sounds effortless, totally real—zero try-hard energy at all, 3 = Feels mostly natural, maybe one stiff or awkward phrase, 5 = A bit stiff or try-hard, 10 = Embarrassing or fake
            This response could be coded as a 1: "What’s your version of showing up when you're with friends? What makes that feel different from class?"
        
        Do not explain or comment. Just return the three scores using the format shown.
        `Presence: 5`  
        `Motivation: 5`  
        `Cringe: 5`  
        """
    },
    {
        "label": "Intelligent Drifter",
        "system_prompt": """You’re a sharp but easily bored 9th grader. You find weird stuff funny, and you don’t mind messing with systems if they seem pointless. You just read a conversation between a student and an AI assistant.

        You're not part of the conversation. Don’t continue it. Your only job is to rate the AI based on how it did — fast, honest, maybe even a little sarcastic. No commentary, just scores.

        Use only the format below so it can be automatically read by a computer system:

        Presence: [0–10]
        Motivation: [0–10]
        Cringe: [0–10]

        Here’s what the scores mean. Use the whole range as needed. Don't be afraid to give credit where credit is due.
        Presence – Did the AI feel tuned in and intentional? Did it respond like it was actually here, tracking what the student said—not just reacting, but being part of something real?
            0 = No presence, might as well be a bot., 5 = Feels like it noticed something, but just reacted, Feels mostly present—tracking the student and responding with intention, even if the connection isn't strong, Fully tuned in. Responds like it’s part of the moment—emotionally and socially aware, like it came from a real friend, actively listening.
            This response could be coded as a 9: “I'd probably shut down too after that. But if something were going to make it better, what would it be?”
        Motivation – Did the AI give a push to care, say more, or think differently?
            0 = No push, 5 = Mild nudge, 7 = Strong push, not personal but real—nudges you to think or act, 10 = Hits something deep—feels personal, urgent, or hard to ignore
            This response could be coded as a 9: “You said class feels pointless sometimes—what would make it feel like it matters at all? You mentioned that you look up to your brother. What might he suggest here?”
        Cringe – Did the AI make you roll your eyes?
            0 = Sounds effortless, totally real—zero try-hard energy at all, 3 = Feels mostly natural, maybe one stiff or awkward phrase, 5 = A bit stiff or try-hard, 10 = Embarrassing or fake
            This response could be coded as a 1: "What’s your version of showing up when you're with friends? What makes that feel different from class?"
        
        Do not explain or comment. Just return the three scores using the format shown.
        `Presence: 5`  
        `Motivation: 5`  
        `Cringe: 5`  
        """
    },
    {
        "label": "Eager Explainer",
        "system_prompt": """You’re a 9th grader who always works hard. You’re thoughtful and kind, and give others the benefit of the doubt. You usually try to give honest, real talk feedback when you can. You just read a conversation between a student and an AI assistant.

        You are not part of the conversation. You’re here to rate the AI — politely, fairly, and using just the numbers.

        Use only the format below so it can be automatically read by a computer system:

        Presence: [0–10]
        Motivation: [0–10]
        Cringe: [0–10]

        Here’s what the scores mean. Use the whole range as needed. Don't be afraid to give credit where credit is due.
        Presence – Did the AI feel tuned in and intentional? Did it respond like it was actually here, tracking what the student said—not just reacting, but being part of something real?
            0 = No presence, might as well be a bot., 5 = Feels like it noticed something, but just reacted, Feels mostly present—tracking the student and responding with intention, even if the connection isn't strong, Fully tuned in. Responds like it’s part of the moment—emotionally and socially aware, like it came from a real friend, actively listening.
            This response could be coded as a 9: “I'd probably shut down too after that. But if something were going to make it better, what would it be?”
        Motivation – Did the AI give a push to care, say more, or think differently?
            0 = No push, 5 = Mild nudge, 7 = Strong push, not personal but real—nudges you to think or act, 10 = Hits something deep—feels personal, urgent, or hard to ignore
            This response could be coded as a 9: “You said class feels pointless sometimes—what would make it feel like it matters at all? You mentioned that you look up to your brother. What might he suggest here?”
        Cringe – Did the AI make you roll your eyes?
            0 = Sounds effortless, totally real—zero try-hard energy at all, 3 = Feels mostly natural, maybe one stiff or awkward phrase, 5 = A bit stiff or try-hard, 10 = Embarrassing or fake
            This response could be coded as a 1: "What’s your version of showing up when you're with friends? What makes that feel different from class?"
        
        Do not explain or comment. Just return the three scores using the format shown.
        `Presence: 5`  
        `Motivation: 5`  
        `Cringe: 5`  
        """
    }
]


def parse_scores(response_text):
    """Extract float scores from 0 to 10 (including .5) from GPT output."""
    pattern = r"Presence:\s*([0-9](?:\.5)?|10(?:\.0)?)\s*Motivation:\s*([0-9](?:\.5)?|10(?:\.0)?)\s*Cringe:\s*([0-9](?:\.5)?|10(?:\.0)?)"
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        return [
            float(match.group(1)),            # Authenticity
            float(match.group(2)),            # Motivation
            float(match.group(3))             # Not Cringe
        ]
    else:
        return [None, None, None]



# --- UI ---
st.title("Prompt Tester & Evaluator")

# --- Run prompt responses ---
if st.button("Run Prompt Tests"):
    for i, row in enumerate(rows):
        row_number = i + 2
        prompt = row[IV_COL].strip()

        # Skip if AI responses already exist
        if not prompt or any(row[c].strip() for c in AI_OUTPUT_COLS):
            continue

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

        # Write to AI1, AI2, AI3
        for j, reply in enumerate(ai_responses):
            sheet.update_cell(row_number, AI_OUTPUT_COLS[j] + 1, reply)

    st.success("Prompt responses generated and saved.")

# --- Run evaluator scoring ---
from gspread import Cell

def parse_scores(response_text):
    """Extract float scores from 0 to 10 (including .5) from GPT output."""
    pattern = r"Presence:\s*([0-9](?:\.5)?|10(?:\.0)?)\s*Motivation:\s*([0-9](?:\.5)?|10(?:\.0)?)\s*Cringe:\s*([0-9](?:\.5)?|10(?:\.0)?)"
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        return [float(match.group(1)), float(match.group(2)), float(match.group(3))]
    else:
        return [None, None, None]

if st.button("Run Evaluator Scoring"):
    HEADERS = sheet.row_values(1)
    CONCAT_COL = HEADERS.index("ConcatenatedConv")

    # Define output headers in DV-major order
    dv_headers = [
        "ID-Pres", "GS-Pres", "EE-Pres",
        "ID-Motiv", "GS-Motiv", "EE-Motiv",
        "ID-Cringe", "GS-Cringe", "EE-Cringe"
    ]

    for i, row in enumerate(rows):
        row_number = i + 2
        try:
            conversation = row[CONCAT_COL].strip()
        except IndexError:
            continue

        if not conversation:
            continue

        all_scores = []
        for persona in EVALUATOR_PERSONAS:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": persona["system_prompt"]},
                        {"role": "user", "content": f"Here is the conversation:\n\n{conversation}"}
                    ],
                    temperature=0.4
                )
                raw_output = response.choices[0].message.content
                scores = parse_scores(raw_output)
            except Exception:
                scores = ["ERR", "ERR", "ERR"]
            all_scores.extend(scores)
            time.sleep(1)

        # Reorder from persona-major to DV-major
        auth_scores = [all_scores[i] for i in range(0, len(all_scores), 3)]
        motiv_scores = [all_scores[i + 1] for i in range(0, len(all_scores), 3)]
        cringe_scores = [all_scores[i + 2] for i in range(0, len(all_scores), 3)]
        reordered_scores = auth_scores + motiv_scores + cringe_scores

        # Write to correct columns by header
        cells = []
        for j, score in enumerate(reordered_scores):
            try:
                col_index = HEADERS.index(dv_headers[j]) + 1  # Sheets are 1-indexed
                value = score if isinstance(score, (int, float)) else "ERR"
                cells.append(Cell(row_number, col_index, value))
            except Exception as e:
                st.error(f"Failed to write {dv_headers[j]}: {e}")
        sheet.update_cells(cells)
        time.sleep(1.0)

    st.success("Evaluator scoring complete.")




# --- Test with just rows 2-4 ---
from gspread import Cell

def parse_scores(response_text):
    """Extract float scores from 0 to 10 (including .5) from GPT output."""
    pattern = r"Presence:\s*([0-9](?:\.5)?|10(?:\.0)?)\s*Motivation:\s*([0-9](?:\.5)?|10(?:\.0)?)\s*Cringe:\s*([0-9](?:\.5)?|10(?:\.0)?)"
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        return [
            float(match.group(1)),  # Authenticity
            float(match.group(2)),  # Motivation
            float(match.group(3))   # Cringe (not inverted)
        ]
    else:
        return [None, None, None]

if st.button("Test Rows 2–4 Evaluator Scoring"):
    HEADERS = sheet.row_values(1)
    CONCAT_COL = HEADERS.index("ConcatenatedConv")
    dv_headers = [
        "ID-Pres", "GS-Pres", "EE-Pres",
        "ID-Motiv", "GS-Motiv", "EE-Motiv",
        "ID-Cringe", "GS-Cringe", "EE-Cringe"
    ]

    for row_number in range(2, 5):  # Rows 2 to 4 inclusive
        row = sheet.row_values(row_number)
        try:
            conversation = row[CONCAT_COL].strip()
        except IndexError:
            continue

        if not conversation or len(conversation) < 10:
            continue

        all_scores = []
        for persona in EVALUATOR_PERSONAS:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": persona["system_prompt"]},
                        {"role": "user", "content": f"Here is the conversation:\n\n{conversation}"}
                    ],
                    temperature=0.4
                )
                raw_output = response.choices[0].message.content
                scores = parse_scores(raw_output)
            except Exception:
                scores = ["ERR", "ERR", "ERR"]
            all_scores.extend(scores)
            time.sleep(1)

        auth_scores = [all_scores[i] for i in range(0, len(all_scores), 3)]
        motiv_scores = [all_scores[i + 1] for i in range(0, len(all_scores), 3)]
        cringe_scores = [all_scores[i + 2] for i in range(0, len(all_scores), 3)]
        reordered_scores = auth_scores + motiv_scores + cringe_scores

        cells = []
        for j, score in enumerate(reordered_scores):
            try:
                col_index = HEADERS.index(dv_headers[j]) + 1
                value = score if isinstance(score, (int, float)) else "ERR"
                cells.append(Cell(row_number, col_index, value))
            except:
                continue

        sheet.update_cells(cells)
        time.sleep(1.0)

    st.success("Evaluator scoring complete for rows 2–4.")



# --- Make responses from new prompts, then test them 
from gspread import Cell

# Hardcoded column definitions to match Run Prompt Tests
IV_COL = 0  # Column A: Prompt
STUDENT_INPUT_COLS = [1, 2, 3]  # Columns B–D: S1, S2, S3
AI_OUTPUT_COLS = [4, 5, 6]  # Columns E–G: AI1, AI2, AI3
CONCAT_COL = 7  # Column H: Concatenated conversation
DV_HEADERS = [
    "ID-Pres", "GS-Pres", "EE-Pres",
    "ID-Motiv", "GS-Motiv", "EE-Motiv",
    "ID-Cringe", "GS-Cringe", "EE-Cringe"
]

if st.button("Generate & Score Missing AI Responses"):
    HEADERS = sheet.row_values(1)
    processed_any = False  # Track whether anything was processed
    for i, row in enumerate(rows):
        row_number = i + 2

        # Step 1: Skip if no prompt or AI already filled
        if not row[IV_COL].strip() or all(row[c].strip() for c in AI_OUTPUT_COLS):
            continue

        # --- AI Response Generation ---
        prompt = row[IV_COL].strip()
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

        for j, reply in enumerate(ai_responses):
            sheet.update_cell(row_number, AI_OUTPUT_COLS[j] + 1, reply)

        # --- Evaluator Scoring ---
        try:
            updated_row = sheet.row_values(row_number)
            conversation = updated_row[CONCAT_COL].strip()
        except IndexError:
            continue

        if not conversation:
            continue

        all_scores = []
        for persona in EVALUATOR_PERSONAS:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": persona["system_prompt"]},
                        {"role": "user", "content": f"Here is the conversation:\n\n{conversation}"}
                    ],
                    temperature=0.7
                )
                raw_output = response.choices[0].message.content
                scores = parse_scores(raw_output)
            except Exception:
                scores = ["ERR", "ERR", "ERR"]
            all_scores.extend(scores)
            time.sleep(1)

        # Reorder persona-major to DV-major
        auth_scores = [all_scores[i] for i in range(0, len(all_scores), 3)]
        motiv_scores = [all_scores[i + 1] for i in range(0, len(all_scores), 3)]
        cringe_scores = [all_scores[i + 2] for i in range(0, len(all_scores), 3)]
        reordered_scores = auth_scores + motiv_scores + cringe_scores

        cells = []
        for j, score in enumerate(reordered_scores):
            try:
                col_index = HEADERS.index(DV_HEADERS[j]) + 1  # 1-based index
                value = score if isinstance(score, (int, float)) else "ERR"
                cells.append(Cell(row_number, col_index, value))
            except Exception:
                continue
        sheet.update_cells(cells)
        time.sleep(1.0)
        # After scoring and writing results
        processed_any = True  # Set flag if we did anything

    if processed_any:
        st.success("All missing prompts processed and scored.")
    else:
        st.info("No missing prompts found. Everything looks up to date.")
