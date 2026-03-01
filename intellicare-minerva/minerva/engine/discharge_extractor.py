"""Extrator simplificado de sumario de alta."""

from __future__ import annotations

import re


CID_PATTERN = re.compile(r"\b([A-Z][0-9]{2}(?:\.[0-9])?)\b")
DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
MED_PATTERN = re.compile(
    r"\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]+)\s+(\d+(?:[.,]\d+)?\s*(?:mg|g|mcg|ml))\s+([0-9xX/ ]+ao dia|1x ao dia|2x ao dia)\b"
)


class DischargeExtractor:
    def extract(self, text: str) -> dict:
        cids = CID_PATTERN.findall(text)
        dates = DATE_PATTERN.findall(text)
        medications = []
        for match in MED_PATTERN.finditer(text):
            medications.append(
                {
                    "name": match.group(1).strip(),
                    "dose": match.group(2).strip(),
                    "frequency": match.group(3).strip(),
                }
            )

        primary = None
        secondary: list[dict[str, str]] = []
        if cids:
            primary = {"cid10": cids[0], "description": None}
            for cid in cids[1:]:
                secondary.append({"cid10": cid, "description": None})

        confidence = 0.9 if (primary or medications) else 0.58
        return {
            "discharge_date": dates[0] if dates else None,
            "primary_diagnosis": primary,
            "secondary_diagnoses": secondary,
            "medications": medications,
            "follow_up": None,
            "instructions": text[:400],
            "confidence_score": confidence,
        }

