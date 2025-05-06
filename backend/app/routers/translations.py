# backend/app/routers/translations.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import TranslationRequest, TranslationResult
from app.dependencies import get_gemini_api_key
from app.services.translation_service import translate_strings
from typing import Dict, List

router = APIRouter()

@router.post("/translate", response_model=TranslationResult)
async def translate_text(
    translation_req: TranslationRequest,
    gemini_api_key: str = Depends(get_gemini_api_key)
):
    """Translate UI strings to a target language"""
    try:
        # Call the translation service
        translations = await translate_strings(
            strings=translation_req.strings,
            target_language=translation_req.target_language,
            contexts=translation_req.contexts,
            api_key=gemini_api_key
        )
        
        return {"translations": translations}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(e)}"
        )

@router.get("/languages", response_model=Dict[str, str])
async def get_supported_languages():
    """Get list of supported languages for translation"""
    return {
        "Arabic": "ar",
        "Bengali": "bn",
        "Chinese (Simplified)": "zh-CN",
        "Chinese (Traditional)": "zh-TW",
        "Dutch": "nl",
        "English": "en",
        "French": "fr",
        "German": "de",
        "Hindi": "hi",
        "Indonesian": "id",
        "Italian": "it",
        "Japanese": "ja",
        "Korean": "ko",
        "Portuguese": "pt",
        "Russian": "ru",
        "Spanish": "es",
        "Swedish": "sv",
        "Thai": "th",
        "Turkish": "tr",
        "Vietnamese": "vi"
    }