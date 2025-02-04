from deepgram import DeepgramClient, PrerecordedOptions
import os
import asyncio

API_Key = "f8af803c1244c35763581248bd4a622819f7992b"


def voice_to_text_deepgram(file_path_audio, output_file_text, language):
    try:
        # Initialize the Deepgram client
        deepgram = DeepgramClient(API_Key)

        transcript_final = []
        transcription_text = []

        # Set transcription options
        options = PrerecordedOptions(
            model="nova-2",
            language=language,
            diarize=True,
            smart_format=True,
        )

        file_path = file_path_audio
        output_file = output_file_text

        with open(file_path, "rb") as audio:
            payload = {
                "buffer": audio,
                "tier": "base",
            }

            response = deepgram.listen.rest.v("1").transcribe_file(payload, options, timeout=300)

        
        current_speaker = None

        for result in response['results']['channels'][0]['alternatives']:
            for word in result['words']:
                speaker = word['speaker']
                start_time = word['start']
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                timestamp = f"[{minutes:02}:{seconds:02}]"
                if current_speaker != speaker:
                    transcription_text.append("\n")
                    if current_speaker is not None:
                        transcription_text.append("\n")
                    current_speaker = speaker
                    transcription_text.append(f"{timestamp} ")
                    transcription_text.append(f"Speaker {speaker}: ")
                transcription_text.append(f"{word['word']} ")

            with open(output_file, 'w', encoding='utf-8') as txt_file:
                txt_file.writelines(transcription_text)
                
        return transcription_text

    except Exception as e:
        print(f"Exception: {e}")
