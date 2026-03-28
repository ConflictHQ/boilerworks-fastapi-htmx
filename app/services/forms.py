def validate_submission(schema: dict, data: dict) -> list[str]:
    """Validate form submission data against a form schema definition.

    Schema format:
    {
        "fields": [
            {"name": "field_name", "type": "text|number|email|select|textarea",
             "required": true, "label": "...", "options": [...]}
        ]
    }
    """
    errors: list[str] = []
    fields = schema.get("fields", [])

    for field in fields:
        name = field.get("name", "")
        required = field.get("required", False)
        field_type = field.get("type", "text")
        value = data.get(name, "")

        if required and not value:
            errors.append(f"{field.get('label', name)} is required")
            continue

        if value and field_type == "number":
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(f"{field.get('label', name)} must be a number")

        if value and field_type == "email" and "@" not in str(value):
            errors.append(f"{field.get('label', name)} must be a valid email")

        if value and field_type == "select":
            options = field.get("options", [])
            if options and str(value) not in [str(o) for o in options]:
                errors.append(f"{field.get('label', name)} must be one of: {', '.join(str(o) for o in options)}")

    return errors
