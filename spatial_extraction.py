from typing import Dict, List

def extract_spatial_key_values(blocks, standard_fields):
    """
    Extract key-value pairs based on spatial alignment of blocks.
    Handles cases where Key and Value are in separate blocks.
    Checks for values:
    1. To the RIGHT of the key (Same line)
    2. BELOW the key (Next line, if no right match found)
    """
    if not blocks:
        return {}
        
    extracted = {}
    
    # Helper to get center Y of a box
    def get_y_center(box):
        ys = [p[1] for p in box]
        return sum(ys) / len(ys)
        
    # Helper to get X range
    def get_x_range(box):
        xs = [p[0] for p in box]
        return min(xs), max(xs)

    # 1. Identify Key Blocks
    key_blocks = []
    value_candidate_blocks = []
    
    # Flatten standard fields for easy lookup
    key_map = {}
    for std_key, variations in standard_fields.items():
        for var in variations:
            key_map[var.lower()] = std_key
            
    for i, block in enumerate(blocks):
        text = block['text'].strip()
        text_lower = text.lower().replace(':', '').strip()
        
        # Exact match or starts with key (e.g. "Name:")
        matched_key = None
        if text_lower in key_map:
            matched_key = key_map[text_lower]
        else:
            # Check if it starts with a key
            for var, std in key_map.items():
                if text_lower.startswith(var) and len(text_lower) < len(var) + 3:
                    matched_key = std
                    break
        
        if matched_key:
            key_blocks.append({
                'index': i,
                'std_key': matched_key,
                'box': block['box'],
                'text': text
            })
        else:
            value_candidate_blocks.append({
                'index': i,
                'box': block['box'],
                'text': text
            })
            
    # 2. Find Values for Keys
    for key_block in key_blocks:
        key_box = key_block['box']
        key_y = get_y_center(key_box)
        key_x_min, key_x_max = get_x_range(key_box)
        key_height = abs(key_box[2][1] - key_box[0][1])
        
        best_val = None
        min_dist = float('inf')
        match_type = None # 'right' or 'below'
        
        # STRATEGY 1: Look for value to the RIGHT
        for val_block in value_candidate_blocks:
            val_box = val_block['box']
            val_y = get_y_center(val_box)
            val_x_min, val_x_max = get_x_range(val_box)
            
            # Check vertical alignment (same line)
            # Tightened tolerance to 0.5x block height to avoid cross-line matches
            y_diff = abs(key_y - val_y)
            if y_diff > key_height * 0.5: 
                continue
                
            # Check horizontal alignment (must be to the right)
            if val_x_min < key_x_max:
                continue
                
            # Calculate distance
            dist = val_x_min - key_x_max
            
            # We want the CLOSEST block to the right, but within reasonable distance
            if dist < min_dist and dist < key_height * 10:
                min_dist = dist
                best_val = val_block
                match_type = 'right'
        
        # STRATEGY 2: If no right match, look BELOW
        if not best_val:
            min_vertical_dist = float('inf')
            
            for val_block in value_candidate_blocks:
                val_box = val_block['box']
                val_y = get_y_center(val_box)
                val_x_min, val_x_max = get_x_range(val_box)
                
                # Must be below
                if val_y <= key_y:
                    continue
                    
                # Check horizontal overlap (must be roughly under the key)
                overlap = max(0, min(key_x_max, val_x_max) - max(key_x_min, val_x_min))
                
                # If no overlap, check if it's slightly to the right but close (indented value)
                is_aligned = overlap > 0 or (val_x_min > key_x_min and val_x_min < key_x_max + key_height * 2)
                
                if not is_aligned:
                    continue
                    
                # Vertical distance
                v_dist = val_y - key_y
                
                # Must be the immediate next line (within 3x height)
                if v_dist < min_vertical_dist and v_dist < key_height * 3:
                    min_vertical_dist = v_dist
                    best_val = val_block
                    match_type = 'below'

        if best_val:
            extracted[key_block['std_key']] = best_val['text']

    # 3. Post-processing: Clean concatenated keys from values
    # e.g. "Ananya SharmaAge" -> "Ananya Sharma"
    # We check if any value ends with a known standard key
    for key, value in extracted.items():
        for std_key, variations in standard_fields.items():
            # Don't strip the key itself (e.g. don't strip "Name" from "Name")
            if key == std_key:
                continue
                
            for var in variations:
                # Check if value ends with this variation (case insensitive)
                # e.g. value="Ananya SharmaAge", var="Age"
                if value.lower().endswith(var.lower()):
                    # Check if it's a suffix (not the whole word)
                    if len(value) > len(var):
                        # Strip it
                        clean_value = value[:-len(var)].strip()
                        extracted[key] = clean_value
                        # Optionally, we could try to assign the stripped part as a new key?
                        # But for now, just cleaning is enough to fix the user's issue.
                        break
            
    return extracted
