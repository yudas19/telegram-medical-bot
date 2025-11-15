import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def test_gemini_models():
    """Test semua model Gemini 2.5 yang mungkin tersedia"""
    genai.configure(api_key=GEMINI_API_KEY)
    
    models_to_test = [
        'gemini-2.0-flash',
        'gemini-2.0-flash-exp',
        'gemini-2.0-pro-exp', 
        'gemini-2.5-flash',
        'gemini-2.5-flash-exp',
        'gemini-2.5-pro-exp',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
    ]
    
    working_models = []
    
    for model_name in models_to_test:
        try:
            print(f"🧪 Testing {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello, test medical question: apa ICD-10 untuk diabetes?")
            print(f"✅ {model_name} - BERHASIL")
            print(f"   Response: {response.text[:100]}...")
            working_models.append(model_name)
            break  # Stop di model pertama yang work
        except Exception as e:
            print(f"❌ {model_name} - {str(e)[:100]}")
    
    print(f"\n🎯 MODEL YANG BERHASIL: {working_models}")
    return working_models

if __name__ == "__main__":
    print("🔍 Testing available Gemini models...")
    test_gemini_models()