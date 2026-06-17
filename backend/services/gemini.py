import os
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*google.generativeai.*", category=FutureWarning)
    import google.generativeai as genai
from backend.config import settings

# Configure Gemini API if key is available
api_key_configured = False
if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        api_key_configured = True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")

def get_mock_explanation(disease_name: str, confidence_score: float, symptoms: list[str]) -> str:
    """
    Fallback mock generator when Gemini API Key is not configured.
    """
    symptoms_str = ", ".join(symptoms)
    return f"""### Educational Summary
Based on the symptoms you entered ({symptoms_str}), our machine learning model identified **{disease_name}** as a possibility (confidence: {confidence_score}%). This information is for educational purposes only.

### Possible Explanation
{disease_name} is a common health condition that can manifest with symptoms like {symptoms_str}. It is often caused by viral infections, minor environmental factors, or temporary immune responses, depending on the exact condition. This is not a diagnosis.

### General Precautions
* **Rest:** Ensure you get adequate sleep (7-8 hours) to help your body recover.
* **Hydration:** Drink plenty of fluids like water, herbal teas, or clear broths.
* **Hygiene:** Wash hands frequently to prevent the spread of common germs.
* **Isolation:** If you suspect a contagious condition, minimize contact with others.

### Lifestyle Recommendations
* **Nutrition:** Eat light, balanced meals rich in vitamins and minerals.
* **Stress Management:** Practice relaxation techniques or deep breathing.
* **Environment:** Rest in a comfortable, well-ventilated room.

### When to Consult a Doctor
> [!IMPORTANT]
> Seek professional medical evaluation if:
> * Symptoms persist for more than 3-5 days without improvement.
> * You experience severe symptoms such as difficulty breathing, high fever that doesn't respond to medication, chest pain, or a severe stiff neck.
> * You have underlying chronic health conditions (e.g., asthma, diabetes, heart disease).

### Safety Note
This content is educational and is not a diagnosis, prescription, or substitute for care from a qualified clinician. If symptoms feel severe, sudden, or dangerous, seek urgent medical help.
"""

def ensure_medical_safety_note(text: str) -> str:
    if not text or not text.strip():
        return ""
    lowered = text.lower()
    if "not a professional diagnosis" in lowered or "not a diagnosis" in lowered:
        return text
    return (
        text.rstrip()
        + "\n\n### Safety Note\nThis is not a professional diagnosis. "
        + "Please consult a qualified healthcare professional for medical advice."
    )

def generate_explanation(disease_name: str, confidence_score: float, symptoms: list[str]) -> str:
    """
    Generates a patient-friendly explanation of the predicted disease using Gemini.
    """
    if not api_key_configured or not settings.GEMINI_API_KEY:
        print("Gemini API key is not configured. Using fallback local response generator.")
        return get_mock_explanation(disease_name, confidence_score, symptoms)
        
    symptoms_str = ", ".join(symptoms)
    
    prompt = f"""
    You are an empathetic, educational health AI assistant. A user has reported the following symptoms: {symptoms_str}.
    Our system has predicted that the user might have: {disease_name} (confidence score: {confidence_score}%).
    
    Please write an educational explanation for the user about {disease_name} based on their symptoms.
    
    You MUST adhere strictly to the following rules:
    1. Structure the response into exactly four sections with these markdown headings:
       ### Possible Explanation
       ### General Precautions
       ### Lifestyle Recommendations
       ### When to Consult a Doctor
    2. Write in simple, reassuring, and patient-friendly language. Avoid complex medical jargon.
    3. Never prescribe or recommend specific medications (e.g., do not suggest taking paracetamol, ibuprofen, antibiotics, etc.). Instead, suggest general supportive care (e.g., resting, staying hydrated).
    4. Never claim certainty. Use language like "may be associated with", "might be", or "often manifests as".
    5. Always state that this is not a professional diagnosis.
    6. Include a markdown warning block under the "When to Consult a Doctor" section specifying clear warning signs (like shortness of breath, high fever, chest pain).
    7. Do not provide dosage instructions, treatment plans, emergency triage decisions, or certainty that the user has the condition.
    8. If symptoms include emergency warning signs, tell the user to seek urgent medical attention without attempting to diagnose the cause.
    
    Provide only the markdown response without any additional conversational text.
    """
    
    try:
        # Use gemini-1.5-flash which is widely available and fast
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "max_output_tokens": 900,
            },
        )
        return ensure_medical_safety_note(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}. Falling back to pre-defined response.")
        return get_mock_explanation(disease_name, confidence_score, symptoms)
