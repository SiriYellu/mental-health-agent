# ML inference for emotion from one-sentence feeling.
# Used only when user provides text; no storage.

from .inference import predict_emotion, get_emotion_tailored_response

__all__ = ["predict_emotion", "get_emotion_tailored_response"]
