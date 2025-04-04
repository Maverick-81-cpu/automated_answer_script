import openai
import base64
import pandas as pd
import os
import re
from datetime import datetime

# Version info: Final version till now. If there is any unrecognized name it will ask for user input to verify.

# Set up OpenAI client with API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
client = openai.OpenAI(api_key=api_key)

# Path to the attendance CSV file
ATTENDANCE_FILE = "attendance.csv"

# Dictionary of student names and roll numbers (ensuring correctness)
STUDENT_DICT = {
    "John Doe": "101",
    "Jane Smith": "102",
    "Bob Johnson": "103",
    "Emily Davis": "104",
    "Michael White": "105"
}


def encode_image_to_base64(image_path):
    """Convert an image file to base64 format."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def clean_name(name):
    """Standardize names by removing numbers, special characters, and extra spaces."""
    name = re.sub(r"[^a-zA-Z\s]", "", name)  # Remove non-alphabetic characters
    return name.strip()


def extract_names_from_image(image_path):
    """Extract handwritten names from an image using OpenAI GPT-4 Vision."""
    base64_image = encode_image_to_base64(image_path)

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an OCR system that extracts handwritten names from images."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": "Extract only the handwritten names from this attendance sheet. Do not include introductory text or numbers."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )

        extracted_text = response.choices[0].message.content.strip()
        extracted_names = extracted_text.split("\n")  # Assuming names are line-separated

        # Clean extracted names
        extracted_names = [clean_name(name) for name in extracted_names if name.strip()]

        print("Extracted Names (Cleaned):", extracted_names)
        return extracted_names

    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return []


def update_attendance(image_path):
    """Update the attendance CSV file with extracted names."""
    extracted_names = extract_names_from_image(image_path)

    if not extracted_names:
        print("No valid names detected. Attendance not updated.")
        return

    # Load existing attendance file if available
    if os.path.exists(ATTENDANCE_FILE):
        existing_df = pd.read_csv(ATTENDANCE_FILE, dtype=str)
        print("Loading the existing attendance file ...")
    else:
        existing_df = pd.DataFrame({"Name": list(STUDENT_DICT.keys()), "Roll Number": list(STUDENT_DICT.values())})
        print("Creating an attendance file ...")

    df = existing_df

    # Get today's date in YYYY-MM-DD format
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Ensure a new column is created for today's attendance
    if today_date not in df.columns:
        df[today_date] = "Absent"  # Default all students to Absent

    # Process each extracted name
    for extracted_name in extracted_names:
        if extracted_name in STUDENT_DICT:
            roll_number = STUDENT_DICT[extracted_name]
            df.loc[df["Roll Number"] == roll_number, today_date] = "Present"
        else:
            print(f"\n⚠️ Unrecognized Name: '{extracted_name}'")
            user_input = input(f"Enter the correct name from the list {list(STUDENT_DICT.keys())}, or type 'skip' to ignore: ").strip()

            if user_input in STUDENT_DICT:
                roll_number = STUDENT_DICT[user_input]
                df.loc[df["Roll Number"] == roll_number, today_date] = "Present"
            elif user_input.lower() == "skip":
                print(f"Skipping attendance for '{extracted_name}'")


    # Save the updated attendance record
    df.to_csv(ATTENDANCE_FILE, index=False)

    print(df)
    print(f"✅ Attendance updated successfully in {ATTENDANCE_FILE}.")


if __name__ == "__main__":
    image_path = input("📷 Enter the path of the scanned attendance sheet: ")
    update_attendance(image_path)
