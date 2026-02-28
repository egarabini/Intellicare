"""FieldFilter — apply hidden/readonly field rules to FHIR resources."""

from __future__ import annotations

from typing import Any


class FieldFilter:
    """Utility to apply hidden and readonly field rules to a FHIR resource dict."""

    @staticmethod
    def apply_hidden(resource: dict[str, Any], hidden_fields: list[str]) -> dict[str, Any]:
        """Return a copy of *resource* with *hidden_fields* removed.

        Supports dot-notation for nested fields: 'meta.security'.
        """
        if not hidden_fields:
            return dict(resource)

        result = dict(resource)
        for field_path in hidden_fields:
            parts = field_path.split(".", 1)
            if len(parts) == 1:
                result.pop(field_path, None)
            else:
                # Nested: e.g. "meta.security" → recurse
                top = parts[0]
                if top in result and isinstance(result[top], dict):
                    result[top] = FieldFilter.apply_hidden(result[top], [parts[1]])

        return result

    @staticmethod
    def get_readonly_fields(
        resource: dict[str, Any], readonly_fields: list[str]
    ) -> dict[str, bool]:
        """Return a dict marking which present fields are read-only.

        Only fields that actually exist in the resource are included.

        Returns:
            {field_name: True} for every field in readonly_fields that exists.
        """
        return {f: True for f in readonly_fields if f in resource}

    @staticmethod
    def apply_meta_extension(
        resource: dict[str, Any], readonly_fields: list[str]
    ) -> dict[str, Any]:
        """Annotate *resource* with FHIR extensions marking readonly fields.

        Adds an extension to resource.meta.extension with
        ``url="urn:intellicare:readonly-field"`` and ``valueString=<field_name>``.
        """
        if not readonly_fields:
            return dict(resource)

        result = dict(resource)
        meta = dict(result.get("meta", {}))
        extensions = list(meta.get("extension", []))

        for field_name in readonly_fields:
            extensions.append(
                {
                    "url": "urn:intellicare:readonly-field",
                    "valueString": field_name,
                }
            )

        meta["extension"] = extensions
        result["meta"] = meta
        return result
