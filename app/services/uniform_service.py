def build_uniform_description(form):
    pieces = []
    for label, hex_key in [
        ("Camisa", "shirt_color_hex"),
        ("Calção", "shorts_color_hex"),
        ("Meião", "socks_color_hex"),
    ]:
        color_hex = (form.get(hex_key) or "").strip().upper()
        if color_hex:
            pieces.append(f"{label}: {color_hex}")
    description = " / ".join(pieces)
    return description or form.get("uniform")


def parse_uniform_description(description):
    if not description:
        return []
    parts = []
    for raw_piece in description.split(" / "):
        if ":" not in raw_piece:
            continue
        label, value = raw_piece.split(":", 1)
        color = value.strip()
        hash_position = color.find("#")
        if hash_position >= 0:
            color = color[hash_position:hash_position + 7].upper()
        if color.startswith("#") and len(color) == 7:
            parts.append({"label": label.strip(), "color": color})
    return parts
