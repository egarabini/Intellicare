"""Assinatura digital de PDFs com certificado PKCS#12 (A1 ICP-Brasil) via pyhanko."""
from __future__ import annotations

import io
import logging

logger = logging.getLogger("intellicare.oswaldo.pdf_signer")


def sign_pdf(pdf_bytes: bytes, pfx_bytes: bytes, pfx_password: str) -> bytes:
    """
    Assina digitalmente um PDF com certificado PKCS#12 (A1 ICP-Brasil).
    Retorna PDF assinado. Lança ValueError se certificado inválido.
    """
    from pyhanko.sign import signers
    from pyhanko.sign.fields import SigFieldSpec
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

    signer = signers.SimpleSigner.load_pkcs12(
        pfx_data=pfx_bytes,
        passphrase=pfx_password.encode(),
    )

    pdf_reader = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes))

    sig_meta = signers.PdfSignatureMetadata(
        field_name="Signature",
        reason="Assinatura Digital ICP-Brasil — CFM 2.299/2021",
        location="IntelliCare",
        certify=False,
    )

    output = io.BytesIO()
    signers.sign_pdf(
        pdf_reader,
        signature_meta=sig_meta,
        signer=signer,
        output=output,
    )
    return output.getvalue()


def extract_certificate_info(pfx_bytes: bytes, pfx_password: str) -> dict:
    """Extrai subject_name e valid_until de um .pfx para armazenamento."""
    from cryptography.hazmat.primitives.serialization import pkcs12

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_bytes,
        pfx_password.encode(),
    )
    if certificate is None:
        raise ValueError("Certificado não encontrado no arquivo .pfx")

    subject = certificate.subject.rfc4514_string()
    valid_until = certificate.not_valid_after_utc.date()

    return {
        "subject_name": subject,
        "valid_until": valid_until,
    }
