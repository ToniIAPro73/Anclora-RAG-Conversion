"""Ingestion helpers for multimedia transcripts, captions, and audio/video files."""
from __future__ import annotations

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Any, Optional

# Whisper for audio transcription
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

# MoviePy for video processing
try:
    from moviepy.editor import VideoFileClip, AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None
    AudioFileClip = None

try:  # pragma: no cover - use real loader when available
    from langchain_community.document_loaders import TextLoader
except Exception:  # pragma: no cover - fallback loader for tests
    from common.text_normalization import Document

    class TextLoader:  # type: ignore[override]
        def __init__(self, file_path: str, encoding: str = "utf8", **_: object) -> None:
            self.file_path = file_path
            self.encoding = encoding

        def load(self):
            with open(self.file_path, "r", encoding=self.encoding) as handle:
                return [Document(page_content=handle.read(), metadata={"source": self.file_path})]

from ..base import BaseFileIngestor

logger = logging.getLogger(__name__)


class AudioTranscriptionLoader:
    """Custom loader for audio files using Whisper transcription."""

    def __init__(self, file_path: str, **kwargs):
        self.file_path = file_path
        self.kwargs = kwargs
        self.model_name = kwargs.get('whisper_model', 'base')

    def load(self) -> List[Any]:
        """Load and transcribe audio file."""
        try:
            if not WHISPER_AVAILABLE:
                return self._create_error_document("Whisper no está disponible. Instale: pip install openai-whisper")

            logger.info(f"Transcribiendo archivo de audio: {self.file_path}")

            # Load Whisper model
            model = whisper.load_model(self.model_name)

            # Transcribe audio
            result = model.transcribe(self.file_path)

            # Create document with transcription
            from common.text_normalization import Document

            # Main transcription document
            main_doc = Document(
                page_content=result["text"],
                metadata={
                    "source": self.file_path,
                    "media_type": "audio",
                    "transcription_model": self.model_name,
                    "language": result.get("language", "unknown"),
                    "duration": self._get_audio_duration(),
                    "segments_count": len(result.get("segments", []))
                }
            )

            documents = [main_doc]

            # Add segment-level documents for detailed analysis
            if "segments" in result:
                for i, segment in enumerate(result["segments"]):
                    segment_doc = Document(
                        page_content=segment["text"],
                        metadata={
                            "source": self.file_path,
                            "media_type": "audio_segment",
                            "segment_id": i,
                            "start_time": segment.get("start", 0),
                            "end_time": segment.get("end", 0),
                            "transcription_model": self.model_name,
                            "language": result.get("language", "unknown")
                        }
                    )
                    documents.append(segment_doc)

            logger.info(f"Transcripción completada: {len(documents)} documentos creados")
            return documents

        except Exception as e:
            logger.error(f"Error transcribiendo audio {self.file_path}: {e}")
            return self._create_error_document(f"Error en transcripción: {str(e)}")

    def _get_audio_duration(self) -> Optional[float]:
        """Get audio duration using moviepy if available."""
        try:
            if MOVIEPY_AVAILABLE:
                with AudioFileClip(self.file_path) as audio:
                    return audio.duration
        except Exception:
            pass
        return None

    def _create_error_document(self, error: str) -> List[Any]:
        """Create error document for failed transcription."""
        from common.text_normalization import Document
        return [Document(
            page_content=f"Error procesando archivo de audio: {error}",
            metadata={
                "source": self.file_path,
                "media_type": "audio",
                "error": error,
                "transcription_status": "failed"
            }
        )]


class VideoTranscriptionLoader:
    """Custom loader for video files using Whisper transcription."""

    def __init__(self, file_path: str, **kwargs):
        self.file_path = file_path
        self.kwargs = kwargs
        self.model_name = kwargs.get('whisper_model', 'base')

    def load(self) -> List[Any]:
        """Load and transcribe video file."""
        try:
            if not WHISPER_AVAILABLE or not MOVIEPY_AVAILABLE:
                missing = []
                if not WHISPER_AVAILABLE:
                    missing.append("openai-whisper")
                if not MOVIEPY_AVAILABLE:
                    missing.append("moviepy")
                return self._create_error_document(f"Dependencias faltantes: {', '.join(missing)}")

            logger.info(f"Procesando archivo de video: {self.file_path}")

            # Extract audio from video
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name

            try:
                # Extract audio using moviepy
                with VideoFileClip(self.file_path) as video:
                    audio = video.audio
                    if audio is None:
                        return self._create_error_document("El video no contiene pista de audio")

                    audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
                    video_duration = video.duration
                    video_fps = video.fps

                # Load Whisper model and transcribe
                model = whisper.load_model(self.model_name)
                result = model.transcribe(temp_audio_path)

                # Create documents
                from common.text_normalization import Document

                # Main transcription document
                main_doc = Document(
                    page_content=result["text"],
                    metadata={
                        "source": self.file_path,
                        "media_type": "video",
                        "transcription_model": self.model_name,
                        "language": result.get("language", "unknown"),
                        "duration": video_duration,
                        "fps": video_fps,
                        "segments_count": len(result.get("segments", []))
                    }
                )

                documents = [main_doc]

                # Add segment-level documents
                if "segments" in result:
                    for i, segment in enumerate(result["segments"]):
                        segment_doc = Document(
                            page_content=segment["text"],
                            metadata={
                                "source": self.file_path,
                                "media_type": "video_segment",
                                "segment_id": i,
                                "start_time": segment.get("start", 0),
                                "end_time": segment.get("end", 0),
                                "transcription_model": self.model_name,
                                "language": result.get("language", "unknown")
                            }
                        )
                        documents.append(segment_doc)

                logger.info(f"Transcripción de video completada: {len(documents)} documentos creados")
                return documents

            finally:
                # Clean up temporary audio file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)

        except Exception as e:
            logger.error(f"Error procesando video {self.file_path}: {e}")
            return self._create_error_document(f"Error en procesamiento: {str(e)}")

    def _create_error_document(self, error: str) -> List[Any]:
        """Create error document for failed processing."""
        from common.text_normalization import Document
        return [Document(
            page_content=f"Error procesando archivo de video: {error}",
            metadata={
                "source": self.file_path,
                "media_type": "video",
                "error": error,
                "transcription_status": "failed"
            }
        )]


MULTIMEDIA_LOADERS = {
    # Subtitle/Caption files (existing)
    ".srt": (TextLoader, {"encoding": "utf8"}),
    ".vtt": (TextLoader, {"encoding": "utf8"}),
    ".sbv": (TextLoader, {"encoding": "utf8"}),
    ".ssa": (TextLoader, {"encoding": "utf8"}),
    # Audio files (new)
    ".mp3": (AudioTranscriptionLoader, {"whisper_model": "base"}),
    ".ogg": (AudioTranscriptionLoader, {"whisper_model": "base"}),
    ".oga": (AudioTranscriptionLoader, {"whisper_model": "base"}),
    # Video files (new)
    ".mp4": (VideoTranscriptionLoader, {"whisper_model": "base"}),
    ".avi": (VideoTranscriptionLoader, {"whisper_model": "base"}),
}

MULTIMEDIA_COLLECTION = "multimedia_assets"


def create_multimedia_ingestor() -> BaseFileIngestor:
    return BaseFileIngestor(
        domain="multimedia",
        collection_name=MULTIMEDIA_COLLECTION,
        loader_mapping=MULTIMEDIA_LOADERS,
    )


MultimediaIngestor = create_multimedia_ingestor()

__all__ = [
    "MULTIMEDIA_COLLECTION",
    "MultimediaIngestor",
    "AudioTranscriptionLoader",
    "VideoTranscriptionLoader",
    "create_multimedia_ingestor",
]
