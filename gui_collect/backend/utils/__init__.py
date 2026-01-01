def is_valid_hash(resource_hash, expected_hash_length=8):
    if len(resource_hash) != expected_hash_length:
        return False

    # Try convert str resource_hash of base 16 to an int
    # If this fails, then the resource_hash is not base 16
    # and is invalid
    try: int(resource_hash, 16)
    except: return False

    return True