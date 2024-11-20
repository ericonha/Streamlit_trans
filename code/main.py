import streamlit as st
import os
from datetime import datetime
import deepgram_process
import openai_process
import io
import re

# Available language options
LANGUAGES = {
    "English": "en",
    "German": "de",
    "Portuguese": "pt-Br",
    "Chinese": "zh"
}

acceptable_formats = [
    "wav",
    "mp3",
    "mp4",
    "mkv"
]


def format_transcript(raw_text):
    """
    Formats a transcript by consolidating timestamps, speaker labels, and their text onto a single line.
    
    Args:
        raw_text (str): The raw transcript text.
    
    Returns:
        str: The formatted transcript.
    """
    # Split the transcript into lines and initialize variables
    lines = raw_text.splitlines()
    formatted_lines = []
    current_line = ""

    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespace
        
        # Check if the line contains a timestamp
        if re.match(r"^\[\d{2}:\d{2}\]$", line):
            # Append the current line to formatted_lines if it's not empty
            if current_line:
                formatted_lines.append(current_line.strip())
                formatted_lines.append("")
                current_line = ""
            current_line = line + " "  # Start a new line with the timestamp
        
        # Check if the line contains a speaker label
        elif re.match(r"^Speaker \d+:$", line):
            current_line += line + " "  # Add speaker label to the current line
        
        # Otherwise, it's part of the speech text
        else:
            current_line += line + " "

    # Add the last line being built, if any
    if current_line:
        formatted_lines.append(current_line.strip())

    # Join all formatted lines with newlines
    return "\n".join(formatted_lines)

# Streamlit app
def main():
    st.title("Transcription Generator with Direct Download")
    st.markdown("""
    This application helps you generate transcriptions from your audio files.
    Simply upload your file, select an output directory, and choose your preferred language.
    Press the button to start the transcription process!
    """)

    # File upload
    st.subheader("Step 1: Upload Your Audio File")
    uploaded_file = st.file_uploader("Choose an audio file (WAV, MP3, MP4, MKV)", type=["wav", "mp3", "mp4", "mkv"])
    
    if uploaded_file:
        st.write(f"Uploaded file: {uploaded_file.name}")

    # Language selection
    st.subheader("Step 2: Select Transcription Language")
    language = st.selectbox("Select a language", list(LANGUAGES.keys()))

    # Choose Output File Name
    st.subheader("Step 3: Choose Output File Name")
    output_filename = st.text_input("Enter the name for your output file", value="transcription.txt")

    # Start transcription button
    if st.button("Start Transcription"):
        if uploaded_file and output_filename:
            language_code = LANGUAGES[language]
            temp_file_path = os.path.join("/tmp", uploaded_file.name)
            transcription_text=[]
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                start_time = datetime.now()

                # Perform transcription
                transcription_text = deepgram_process.voice_to_text_deepgram(
                    temp_file_path, 
                    "/tmp/" + output_filename, 
                    language_code
                )
                
                # Ensure transcription_text is a string, not a list
                if isinstance(transcription_text, list):
                    transcription_text = "\n".join(transcription_text)  # Join list elements into a single string

                # Record end time and display results
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                st.success(f"Transcription completed in {duration:.2f} seconds.")
                st.write(f"Transcription ready for download as {output_filename}")

                formatted_transcription = format_transcript(transcription_text)  

                # Provide download button for transcription text
                st.download_button(
                    label="Download Transcription",
                    data=formatted_transcription,
                    file_name=output_filename,
                    mime="pdf"
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Ensure you upload a file and provide a file name.")

if __name__ == "__main__":
    main()
