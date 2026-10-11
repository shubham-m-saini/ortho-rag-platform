import os
import sys
import json
import whisper
import torch
from pathlib import Path

def transcribe_audio(audio_path):
    """
    Transcribes an existing audio file using Whisper.
    Returns the transcript text and segments.
    """
    
    # Check if MPS (Apple GPU) is available for faster processing
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"⚡ Running on: {device}")

    print(f"\n🎤 Step 1: Loading Whisper model...")
    
    try:
        # Load 'base' model. 
        # Use 'small' or 'large' for better medical accuracy if you have enough RAM/GPU.
        model = whisper.load_model("base", device=device) 
    except Exception as e:
        print(f"❌ Error loading Whisper model: {e}")
        return None, None

    print(f"🎙️ Step 2: Transcribing audio file...")
    
    try:
        result = model.transcribe(audio_path)
        transcript_text = result["text"]
        segments = result.get("segments", [])
        
        if not transcript_text.strip():
            print("⚠️ Warning: Transcription returned empty text.")
            
        return transcript_text, segments
        
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return None, None

def main():
    # Expecting the audio file path as an argument
    if len(sys.argv) < 2:
        print("❌ Usage: python transcribe_worker.py <path_to_audio_file>")
        return

    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"❌ Error: Audio file not found at {audio_path}")
        return

    # Extract video ID from filename (e.g., hzTwjmM09JA.mp3 -> hzTwjmM09JA)
    video_id = Path(audio_path).stem
    
    print(f"🚀 Starting Transcription for: {video_id}")

    text, segments = transcribe_audio(audio_path)
    
    if text:
        output_dir = "transcripts"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Prepare the data dictionary cleanly
        final_data = {
            "video_id": video_id,
            "title": f"Transcript for {video_id}", 
            "transcript": text,
            "segments": segments if segments else []
        }

        filename = f"{output_dir}/{video_id}_transcript.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Transcript saved to: {filename}")
            print(f"📝 Length: {len(text)} characters")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
    else:
        print("❌ Transcription failed.")

if __name__ == "__main__":
    main()
