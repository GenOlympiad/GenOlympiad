# code: parse_code
def parse_block_height(raw):
    """The block height as an integer from the API reply, or None if it cannot be read."""
    try:
        if isinstance(raw, dict):
            return {'height': int(raw.get('height'))}
        return {'height': int(str(raw).strip())}
    except Exception:
        return {'height': None}

# end of parse_code
