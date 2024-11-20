import streamlit as st
import os
from datetime import datetime
import git.Streamlit_trans.code.deepgram_process as deepgram_process
import git.Streamlit_trans.code.openai_process as openai_process
from multiprocessing import Pool, cpu_count

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

# Function to map participant names (for parallelization)
def map_participant_name(args):
    placeholder, updated_name, text = args
    return text.replace(placeholder, updated_name)

# Streamlit app
def main():
    st.title("Transcription Generator with Parallel Processing")
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

    # Folder path input
    st.subheader("Step 3: Enter Output Directory Path")
    selected_folder_path = st.text_input("Enter the full path for the output directory", value="")

    # Choose Output File Name
    st.subheader("Step 4: Choose Output File Name")
    output_filename = st.text_input("Enter the name for your output file", value="transcription.txt")

    # Start transcription button
    if st.button("Start Transcription"):
        if uploaded_file and os.path.exists(selected_folder_path) and output_filename:
            language_code = LANGUAGES[language]
            temp_file_path = os.path.join("/tmp", uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                start_time = datetime.now()

                # Perform transcription
                transcription_text = deepgram_process.voice_to_text_deepgram(
                    temp_file_path, 
                    os.path.join(selected_folder_path, output_filename), 
                    language_code
                )
                
                transcription_text = openai_process.openai_trans(
                    transcription_text, 
                    os.path.join(selected_folder_path, output_filename)
                )

                # Record end time and display results
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                st.success(f"Transcription completed in {duration:.2f} seconds.")
                st.write(f"Transcription saved to {selected_folder_path}/{output_filename}")

                # Save transcription text to session state
                st.session_state.transcription_text = transcription_text

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Ensure you upload a file, specify a valid directory, and provide a file name.")

    # Participant Mapping
    if 'transcription_text' in st.session_state:
        transcription_text = st.session_state.transcription_text

        st.subheader("Step 5: Map Participant Names")
        participants = detect_participants(transcription_text)

        if participants:
            st.write("Detected participants:")
            st.write(", ".join(participants))
            updated_names = [
                st.text_input(f"Enter name for {p}:", value=p) for p in participants
            ]

            if st.button("Generate Updated File"):
                # Parallel name replacement
                with Pool(cpu_count()) as pool:
                    updated_transcription = pool.map(
                        map_participant_name,
                        [(p, n, transcription_text) for p, n in zip(participants, updated_names)]
                    )
                
                # Combine results into a single string
                final_transcription = "".join(updated_transcription)

                # Save updated file
                updated_file_path = os.path.join(selected_folder_path, f"updated_{output_filename}")
                with open(updated_file_path, "w") as f:
                    f.write(final_transcription)

                st.success(f"Updated transcription saved to {updated_file_path}")
                st.markdown("### Updated Transcription")
                st.write(final_transcription)

# Helper function to detect participants
def detect_participants(text):
    import re
    return re.findall(r"Participant \d+", text)

if __name__ == "__main__":
    main()
