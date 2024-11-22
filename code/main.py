import streamlit as st
import os
from datetime import datetime
import deepgram_process
import re
from fpdf import FPDF

LANGUAGES = {
    "English": "en",
    "German": "de",
    "Portuguese": "pt-Br",
    "Chinese": "zh"
}

def format_transcript(raw_text):
    lines = raw_text.splitlines()
    formatted_lines = []
    current_line = ""

    for line in lines:
        line = line.strip()
        if re.match(r"^\[\d{2}:\d{2}\]$", line):
            if current_line:
                formatted_lines.append(current_line.strip())
                formatted_lines.append("")
                current_line = ""
            current_line = line + " "
        elif re.match(r"^Speaker \d+:$", line):
            current_line += line + " "
        else:
            current_line += line + " "

    if current_line:
        formatted_lines.append(current_line.strip())

    return "\n".join(formatted_lines)

class StyledPDF(FPDF):
    def header(self):
        # Add a title header with a large bold font
        self.set_font("Arial", style="B", size=16)
        self.cell(0, 10, "Transcription Document", ln=True, align="C")
        self.ln(10)  # Add vertical spacing

    def footer(self):
        # Add a page number at the bottom
        self.set_y(-15)  # Position 15mm from the bottom
        self.set_font("Arial", size=8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf(content, output_file):
    pdf = StyledPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Default font style
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)  # Black for all text

    for line in content.splitlines():
        # Split line into parts based on square brackets
        parts = re.split(r"(\[.*?\])", line)
        for part in parts:
            if part.startswith("[") and part.endswith("]"):  # Italicize content in square brackets
                pdf.set_font("Arial", style="I", size=12)  # Italic font
            else:  # Render normal text for other parts
                pdf.set_font("Arial", style="", size=12)  # Normal font

            pdf.cell(0, 10, txt=part, ln=False)  # Render text inline

        pdf.ln(10)  # Move to the next line after completing a line

    pdf.output(output_file)
    return output_file


def main():
    st.title("Transcription Generator with Direct Download")
    st.markdown("Upload an audio file, select language, and generate a transcription.")
    transcription_text = ""
    uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "mp4", "mkv"])
    if uploaded_file:
        st.write(f"Uploaded file: {uploaded_file.name}")

    language = st.selectbox("Select a language", list(LANGUAGES.keys()))
    output_filename = st.text_input("Enter the name for your output file", value="transcription.txt")

    if st.button("Start Transcription"):
        if uploaded_file and output_filename:
            language_code = LANGUAGES[language]
            temp_file_path = os.path.join("/tmp", uploaded_file.name)
            transcription_text = ""

            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                start_time = datetime.now()
                transcription_text = deepgram_process.voice_to_text_deepgram(
                    temp_file_path, 
                    "/tmp/" + output_filename, 
                    language_code
                )
                if isinstance(transcription_text, list):
                    transcription_text = "\n".join(transcription_text)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                st.success(f"Transcription completed in {duration:.2f} seconds.")
                st.write(f"Transcription ready for download as {output_filename}")

                formatted_transcription = ""
                formatted_transcription = format_transcript(transcription_text)  

                pdf_file_path = "/tmp/transcription.pdf"
                generate_pdf(formatted_transcription, pdf_file_path)

                with open(pdf_file_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download Transcription (PDF)",
                        data=pdf_file,
                        file_name="transcription.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Ensure you upload a file and provide a file name.")

if __name__ == "__main__":
    main()
