# app/tts_module.py
#from gtts import gTTS
#import os, uuid

#TTS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "tts")
#os.makedirs(TTS_DIR, exist_ok=True)

#def text_to_mp3(text: str, lang="ko") -> str:
#   """텍스트를 MP3로 변환하고 파일명(예: 'a1b2c3d4.mp3')을 반환."""
#  fname = f"{uuid.uuid4().hex[:8]}.mp3"
#    out_path = os.path.join(TTS_DIR, fname)
#    tts = gTTS(text=text, lang=lang)
#    tts.save(out_path)
#    return fname
