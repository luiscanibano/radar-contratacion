"""Plantilla visual común para los emails transaccionales (verificación, reset
de contraseña, alertas). HTML por tablas + estilos inline a propósito: es lo
único que sobrevive de forma fiable a Gmail/Outlook, que no fían de <style>.

Los colores replican los tokens de marca de web/src/index.css (--primary,
--foreground, --muted-foreground, --border) en hexadecimal, porque los
clientes de email no soportan variables CSS.
"""

from __future__ import annotations

import re

_AZUL_MARCA = "#1e40af"
_TEXTO = "#0f172a"
_TEXTO_SECUNDARIO = "#64748b"
_BORDE = "#e2e8f0"
_FONDO = "#f8fafc"


def _boton(texto: str, url: str) -> str:
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0;">
      <tr>
        <td style="border-radius:999px;background:{_AZUL_MARCA};">
          <a href="{url}"
             style="display:inline-block;padding:12px 28px;font-family:'IBM Plex Sans',Arial,sans-serif;
                    font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:999px;">
            {texto}
          </a>
        </td>
      </tr>
    </table>"""


def plantilla_email(
    titulo: str,
    cuerpo_html: str,
    cta_texto: str | None = None,
    cta_url: str | None = None,
    pie_contexto: str = (
        "Recibes este email porque tienes una cuenta en Radar de Contratación Pública."
    ),
) -> tuple[str, str]:
    """Envuelve `cuerpo_html` en la plantilla de marca. Devuelve (html, texto_plano)."""
    boton_html = _boton(cta_texto, cta_url) if cta_texto and cta_url else ""
    cta_texto_plano = f"\n\n{cta_texto}: {cta_url}" if cta_texto and cta_url else ""

    html = f"""\
<!doctype html>
<html lang="es">
  <body style="margin:0;padding:32px 16px;background:{_FONDO};
               font-family:'IBM Plex Sans',Arial,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" style="max-width:480px;" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding-bottom:24px;">
                <span style="font-size:16px;font-weight:700;letter-spacing:-0.01em;color:{_AZUL_MARCA};">
                  Radar de Contratación Pública
                </span>
              </td>
            </tr>
            <tr>
              <td style="background:#ffffff;border:1px solid {_BORDE};border-radius:16px;padding:32px;">
                <h1 style="margin:0 0 16px;font-size:19px;font-weight:600;letter-spacing:-0.01em;color:{_TEXTO};">
                  {titulo}
                </h1>
                <div style="font-size:14px;line-height:1.6;color:{_TEXTO};">
                  {cuerpo_html}
                </div>
                {boton_html}
              </td>
            </tr>
            <tr>
              <td style="padding-top:24px;font-size:12px;line-height:1.6;color:{_TEXTO_SECUNDARIO};">
                <p style="margin:0 0 8px;">{pie_contexto}</p>
                <p style="margin:0;">
                  <a href="https://radarcontratacion.com/legal#privacidad" style="color:{_TEXTO_SECUNDARIO};">Privacidad</a>
                  &nbsp;·&nbsp;
                  <a href="https://radarcontratacion.com/legal#terminos" style="color:{_TEXTO_SECUNDARIO};">Términos de uso</a>
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""

    texto_plano = (
        f"{titulo}\n\n{re.sub('<[^>]+>', '', cuerpo_html).strip()}{cta_texto_plano}\n\n"
        f"{pie_contexto}\n"
        "Privacidad: https://radarcontratacion.com/legal#privacidad\n"
        "Términos de uso: https://radarcontratacion.com/legal#terminos"
    )
    return html, texto_plano
