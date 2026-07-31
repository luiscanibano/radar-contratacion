"""Tests de api/email_templates.py: la plantilla común de los emails."""

from __future__ import annotations

from api.email_templates import plantilla_email


def test_incluye_marca_titulo_y_cuerpo():
    html, _ = plantilla_email("Confirma tu cuenta", "<p>hola</p>")
    assert "Radar de Contratación Pública" in html
    assert "Confirma tu cuenta" in html
    assert "<p>hola</p>" in html


def test_incluye_enlaces_legales_en_html_y_texto():
    html, texto = plantilla_email("Título", "<p>cuerpo</p>")
    assert "radarcontratacion.com/legal#privacidad" in html
    assert "radarcontratacion.com/legal#terminos" in html
    assert "radarcontratacion.com/legal#privacidad" in texto
    assert "radarcontratacion.com/legal#terminos" in texto


def test_boton_cta_solo_aparece_si_se_pasan_texto_y_url():
    con_cta_html, con_cta_texto = plantilla_email(
        "Título", "<p>cuerpo</p>", cta_texto="Confirmar", cta_url="https://x/y"
    )
    sin_cta_html, sin_cta_texto = plantilla_email(
        "Título",
        "<p>cuerpo</p>",
        cta_texto="Confirmar",  # falta cta_url: no debe pintarse
    )

    assert "https://x/y" in con_cta_html
    assert "https://x/y" in con_cta_texto
    assert "Confirmar" not in sin_cta_html
    assert "Confirmar" not in sin_cta_texto


def test_texto_plano_no_contiene_etiquetas_html():
    _, texto = plantilla_email("Título", "<p>hola <strong>mundo</strong></p>")
    assert "<p>" not in texto
    assert "<strong>" not in texto
    assert "hola" in texto and "mundo" in texto
