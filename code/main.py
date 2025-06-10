import streamlit as st
import os
from datetime import datetime
import deepgram_process
import re
from fpdf import FPDF

LANGUAGES = {
    "German": "de",
    "English": "en",
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
    def footer(self):
        # Add a page number at the bottom
        self.set_y(-15)  # Position 15mm from the bottom
        self.set_font("Arial", size=8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_pdf(content, output_file):
    pdf = StyledPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Default font style
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)  # Black for all text

    for line in content.splitlines():
        if line.startswith("[") and "]" in line:  # Italicize timestamps
            pdf.set_font("Arial", style="I", size=12)  # Italic font
        else:  # Normal text for other lines
            pdf.set_font("Arial", style="", size=12)  # Normal font

        pdf.multi_cell(0, 10, txt=line)  # Add line with word wrapping

    pdf.output(output_file)
    return output_file

def main():
    st.title("Transcription Generator with Direct Download")
    st.markdown("Upload an audio file, select language, and generate a transcription.")

    uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "mp4", "mkv"])
    language = st.selectbox("Select a language", list(LANGUAGES.keys()))

    if uploaded_file:
        st.write(f"Uploaded file: {uploaded_file.name}")

        base_name = os.path.splitext(uploaded_file.name)[0]
        output_pdf_name = f"{base_name}_transcript.pdf"
        output_pdf_path = os.path.join("/tmp", output_pdf_name)
        temp_file_path = os.path.join("/tmp", uploaded_file.name)

        if st.button("Start Transcription"):
            try:
                language_code = LANGUAGES[language]

                # Save uploaded audio file temporarily
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                start_time = datetime.now()
                transcription_text = deepgram_process.voice_to_text_deepgram(
                    temp_file_path,
                    output_pdf_path,
                    language_code
                )

                if isinstance(transcription_text, list):
                    transcription_text = "\n".join(transcription_text)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                st.success(f"Transcription completed in {duration:.2f} seconds.")
                st.write(f"Transcription ready for download as {output_pdf_name}")

                formatted_transcription = format_transcript(transcription_text)
                generate_pdf(formatted_transcription, output_pdf_path)

                with open(output_pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download Transcription (PDF)",
                        data=pdf_file,
                        file_name=output_pdf_name,
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload an audio file before starting transcription.")

if __name__ == "__main__":
    main()
