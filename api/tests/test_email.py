"""Tests de api/email.py: nunca habla con Resend de verdad (httpx mockeado)."""

from __future__ import annotations

from unittest.mock import Mock, patch

import httpx
import pytest

from api.email import enviar_email
from api.settings import settings


def test_sin_api_key_lanza_value_error(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "")
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        enviar_email("a@b.com", "asunto", "<p>hola</p>")


def test_envio_exitoso_llama_a_resend_con_los_datos_correctos(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_falsa")
    monkeypatch.setattr(settings, "alert_from_email", "alertas@radarcontratacion.com")
    respuesta_falsa = Mock()
    respuesta_falsa.raise_for_status = Mock()

    with patch("httpx.post", return_value=respuesta_falsa) as mock_post:
        enviar_email("destino@example.com", "asunto", "<p>hola</p>")

    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer re_falsa"
    assert kwargs["json"] == {
        "from": "alertas@radarcontratacion.com",
        "to": ["destino@example.com"],
        "subject": "asunto",
        "html": "<p>hola</p>",
    }
    respuesta_falsa.raise_for_status.assert_called_once()


def test_error_de_resend_se_propaga(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_falsa")
    respuesta_falsa = Mock()
    respuesta_falsa.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError("403", request=Mock(), response=Mock())
    )

    with patch("httpx.post", return_value=respuesta_falsa):
        with pytest.raises(httpx.HTTPStatusError):
            enviar_email("destino@example.com", "asunto", "<p>hola</p>")
