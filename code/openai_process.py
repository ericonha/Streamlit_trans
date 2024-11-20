import re
from openai import OpenAI
import tiktoken

# Your API key
Open_Ai_Key = "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"

# Initialize OpenAI client
client = OpenAI(api_key=Open_Ai_Key)

# Initialize token encoder for GPT-4 (or GPT-4o-mini)
encoding = tiktoken.get_encoding("cl100k_base")

def filter_transcription(raw_transcription_list):
    """
    Cleans up a list of transcription lines by removing timestamps and unnecessary symbols,
    while preserving speaker labels and their dialogue. It returns a list of cleaned-up strings.
    """
    cleaned_transcription_list = []
    
    # Iterate through each line in the transcription list
    for line in raw_transcription_list:
        # Remove timestamps (patterns like [00:03])
        cleaned_line = re.sub(r'\[\d{2}:\d{2}\]', '', line)
        
        # Remove extra spaces or unnecessary newlines
        cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
        
        # Ensure each speaker starts on a new line (if needed)
        cleaned_line = re.sub(r'(Speaker \d+:)', r'\n\1', cleaned_line)
        
        # Remove leading/trailing whitespaces
        cleaned_line = cleaned_line.strip()
        
        # Append the cleaned line to the result list
        cleaned_transcription_list.append(cleaned_line)
    
    return cleaned_transcription_list

def split_into_chunks(text, max_tokens=16384):
    """
    Splits the text into chunks of a specified token limit.

    Args:
    - text (str): The full transcription as a string.
    - max_tokens (int): The maximum number of tokens per chunk.

    Returns:
    - list: A list of text chunks.
    """
    tokens = encoding.encode(text)
    chunks = []
    
    # Split the tokens into chunks of the desired size
    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(encoding.decode(chunk))
    
    return chunks

def process_with_context(chunks):
    """
    Processes chunks sequentially, maintaining context across chunks.
    Only generates the final summary.
    """
    context_summary = ""
    
    for i, chunk in enumerate(chunks):
        prompt = f"""
        You are an assistant that summarizes and maintains context across a conversation.
        The following transcription is part of a meeting. Your task is to process the conversation and keep a running summary of the meeting.

        Previous summary:
        {context_summary}
        
        Current chunk:
        {chunk}

        Provide a concise summary of the current chunk and update the summary.

        Updated summary:
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a summarizer assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            
            # Capture the updated summary from the model
            context_summary = response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error processing chunk {i + 1}: {e}")
            continue

    # Final summary of the entire meeting, with the required structure
    final_summary = f"Summary:\n{context_summary}"
    return final_summary

def openai_trans(data, output_file):
    """
    Function that filters the transcription, processes it through OpenAI API, and writes the result to a file.
    """
    # Clean the transcription
    data_new = filter_transcription(data)
    
    # Join the cleaned data into a single string for token calculation and splitting
    full_text = " ".join(data_new)

    # Split the full transcription into manageable chunks
    chunks = split_into_chunks(full_text)

    # Process the chunks while maintaining context
    final_summary = process_with_context(chunks)

    # Output file name with "_openai" suffix
    output_file_tmp = str.split(output_file, ".")[0] + "_openai.txt"

    # Save the final summary to the output file
    with open(output_file_tmp, 'w', encoding='utf-8') as txt_file:
        txt_file.writelines(final_summary)

    return final_summary
