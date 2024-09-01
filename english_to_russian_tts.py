import os
from dotenv import load_dotenv
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from openai import OpenAI
import sys
import time
import random

# Load environment variables
load_dotenv()

# Set up API clients
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not elevenlabs_api_key or not openai_api_key:
    print("Error: API keys not found in environment variables.")
    sys.exit(1)

elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
openai_client = OpenAI(api_key=openai_api_key)

def verify_api_key():
    try:
        elevenlabs_client.voices.get_all()
        return True
    except Exception as e:
        print(f"Error verifying ElevenLabs API key: {e}")
        return False

def translate_and_detect(text):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator. Detect the language of the input text and translate it to the other language (English to Russian or Russian to English). Respond in the format 'Detected Language: [language]\nTranslation: [translation]'."},
                {"role": "user", "content": f"Translate this text: {text}"}
            ]
        )
        result = response.choices[0].message.content.strip()
        
        detected_language = None
        translation = None
        
        for line in result.split('\n'):
            if line.startswith("Detected Language:"):
                detected_language = line.split(":")[1].strip()
            elif line.startswith("Translation:"):
                translation = line.split(":", 1)[1].strip()
        
        if not detected_language or not translation:
            raise ValueError("Unexpected response format from OpenAI")
        
        return detected_language, translation
    except Exception as e:
        print(f"Error in OpenAI translation: {e}")
        return None, None

def transliterate_russian(text):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a transliteration tool. Provide the English transliteration of the given Russian text to help with pronunciation."},
                {"role": "user", "content": f"Transliterate this Russian text: {text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in OpenAI transliteration: {e}")
        return None

def get_available_voices():
    try:
        voices = elevenlabs_client.voices.get_all()
        return {voice.name: voice.voice_id for voice in voices.voices}
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return {}

def get_available_models():
    try:
        models = elevenlabs_client.models.get_all()
        return [model.model_id for model in models.models]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return ["eleven_multilingual_v2"]  # Fallback to a default model

def text_to_speech_with_elevenlabs(text, voice_name, model):
    try:
        voices = get_available_voices()
        if voice_name not in voices:
            print(f"Voice '{voice_name}' not found. Available voices: {', '.join(voices.keys())}")
            voice_name, voice_id = next(iter(voices.items())) if voices else (None, None)
            if not voice_id:
                raise Exception("No voices available")
            print(f"Using default voice: {voice_name}")
        else:
            voice_id = voices[voice_name]
        
        audio = elevenlabs_client.generate(
            text=text,
            voice=voice_id,
            model=model
        )
        play(audio)
    except Exception as e:
        print(f"Error in ElevenLabs text-to-speech: {e}")

def process_and_speak(text, voice_name, model):
    detected_language, translation = translate_and_detect(text)
    
    if detected_language and translation:
        print(f"Detected language: {detected_language}")
        print(f"{'English' if detected_language.lower() == 'russian' else 'Russian'}: {translation}")
        
        if detected_language.lower() == "russian":
            transliteration = transliterate_russian(text)
            if transliteration:
                print(f"Pronunciation guide: {transliteration}")
        
        print(f"Using model: {model}")
        print(f"Using voice: {voice_name}")
        print("Playing original text:")
        text_to_speech_with_elevenlabs(text, voice_name, model)
        time.sleep(1)
        print("Playing translation:")
        text_to_speech_with_elevenlabs(translation, voice_name, model)
    else:
        print("Translation failed. Please try again.")

def main():
    if not verify_api_key():
        print("Invalid ElevenLabs API key. Please check your credentials.")
        sys.exit(1)

    print("Welcome to the English-Russian Translator and Pronunciation Helper!")
    print("Enter text in English or Russian to hear its translation and pronunciation.")
    print("Type 'quit' to exit the program.")
    
    voices = get_available_voices()
    if not voices:
        print("No voices available. Using default settings.")
    else:
        print(f"Available voices: {', '.join(voices.keys())}")
    
    # Get available models
    models = get_available_models()
    
    while True:
        text = input("\nEnter text in English or Russian (or 'quit' to exit): ").strip()
        if text.lower() == 'quit':
            break
        
        # Choose a random model and voice for each translation
        model = random.choice(models)
        voice_name = random.choice(list(voices.keys())) if voices else None
        
        process_and_speak(text, voice_name, model)
        time.sleep(1)  # Add a small delay to avoid potential rate limiting

    print("Thank you for using the translator!")

if __name__ == "__main__":
    main()