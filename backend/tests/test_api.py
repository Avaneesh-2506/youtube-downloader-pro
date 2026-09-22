import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ytdl_service import is_valid_youtube_url, sanitize_filename, format_duration, format_bytes
from app.services.ffmpeg_locator import get_ffmpeg_path

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ffmpeg_ready" in data

def test_youtube_url_validator():
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    for url in valid_urls:
        assert is_valid_youtube_url(url) is True, f"Failed on valid URL: {url}"

    invalid_urls = [
        "https://google.com",
        "https://vimeo.com/123456",
        "invalid-url",
        "https://youtube.com",
    ]
    for url in invalid_urls:
        assert is_valid_youtube_url(url) is False, f"Failed on invalid URL: {url}"

def test_sanitize_filename():
    unsafe = 'Video: Test / Sample * "Question" <Tag> | Slash'
    safe = sanitize_filename(unsafe)
    assert ":" not in safe
    assert "/" not in safe
    assert "*" not in safe
    assert '"' not in safe
    assert "<" not in safe
    assert ">" not in safe
    assert "|" not in safe
    assert safe == "Video Test  Sample  Question Tag  Slash"

def test_format_helpers():
    assert format_duration(65) == "01:05"
    assert format_duration(3665) == "01:01:05"
    assert format_duration(0) == "00:00"
    
    assert "MB" in format_bytes(15 * 1024 * 1024)
    assert format_bytes(None) == "Unknown"

def test_info_endpoint_invalid_url():
    response = client.post("/api/v1/info", json={"url": "https://notyoutube.com/test"})
    assert response.status_code == 422

def test_ffmpeg_detection():
    path = get_ffmpeg_path()
    assert path is not None, "FFmpeg should be detected either from system or imageio-ffmpeg"
