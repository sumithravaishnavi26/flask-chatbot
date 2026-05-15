import google.generativeai as genai

# ✅ configure your Gemini API key
genai.configure(api_key="AIzaSyAKJOv4MVoH262-yL_h7ld_rBTH3oV3HW4")

# ✅ list all available models
print("Available models:")
for model in genai.list_models():
    print(model.name)
