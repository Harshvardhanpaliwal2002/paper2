import pdfplumber
import re
from collections import Counter

def parse_pdf(file_obj):
    """
    Parses a PDF file object and extracts Title, Authors, and Sections based on font size and styling.
    Returns a dictionary with the extracted data.
    """
    extracted_data = {}
    
    with pdfplumber.open(file_obj) as pdf:
        all_lines = []
        
        # --- 1. Extract all lines with font info ---
        for page in pdf.pages:
            # Get all characters
            chars = page.chars
            if not chars:
                continue
                
            # Sort characters by Y (top) then X (x0)
            # Rounding 'top' helps group chars on the same line
            chars.sort(key=lambda c: (round(c['top'], 1), c['x0']))
            
            current_line_chars = []
            last_top = 0
            
            for char in chars:
                if not current_line_chars:
                    current_line_chars.append(char)
                    last_top = char['top']
                    continue
                
                # Check if on same line (within tolerance)
                if abs(char['top'] - last_top) < 3: 
                    current_line_chars.append(char)
                else:
                    # Process completed line
                    all_lines.append(process_line(current_line_chars))
                    current_line_chars = [char]
                    last_top = char['top']
            
            if current_line_chars:
                all_lines.append(process_line(current_line_chars))

    if not all_lines:
        return extracted_data

    # --- 2. Identify Title (Largest Text) ---
    # Find max font size in the document
    max_size = max(line['font_size'] for line in all_lines)
    
    # Title is lines with max_size (or very close, e.g., > 95%)
    title_lines = [line for line in all_lines if line['font_size'] >= max_size * 0.95]
    
    # Combine title lines
    extracted_data['Title'] = " ".join([l['text'] for l in title_lines]).strip()
    
    # Find the index of the last title line to know where to start looking for Authors
    # We use the index in all_lines. Note: title_lines might not be contiguous if there's noise, 
    # but usually they are at the top. We'll take the max index of any title line.
    title_indices = [all_lines.index(l) for l in title_lines]
    last_title_index = max(title_indices) if title_indices else -1
    
    # --- 3. Identify Authors ---
    # Authors are text after Title but before the first Section (usually Abstract)
    # We need to find where "Abstract" starts to define the Author range.
    
    start_index = last_title_index + 1
    abstract_index = -1
    
    # Look for "Abstract" to define end of Authors
    for i in range(start_index, len(all_lines)):
        text_lower = all_lines[i]['text'].lower()
        if "abstract" in text_lower:
            abstract_index = i
            break
            
    if abstract_index != -1:
        # Authors are between Title and Abstract
        authors_lines = all_lines[start_index : abstract_index]
        
        # Clean Author Text
        cleaned_authors = []
        for l in authors_lines:
            text = l['text']
            
            # Filter out metadata lines (Accepted, Published, Copyright)
            # Check case-insensitive
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ["accepted:", "published:", "©", "copyright", "received:"]):
                continue
                
            # Remove digits (e.g. affiliation numbers)
            text = re.sub(r'\d+', '', text)
            
            # Remove unwanted symbols (user specified ⟩⟩⟩ and potentially others)
            # We'll remove the specific ones and common replacement chars
            text = re.sub(r'[⟩]', '', text)
            
            cleaned_text = text.strip()
            if cleaned_text:
                cleaned_authors.append(cleaned_text)
                
        extracted_data['Authors'] = "\n".join(cleaned_authors).strip()
        
        # Start processing sections from Abstract
        current_index = abstract_index
    else:
        # No Abstract found? Fallback: Take next few lines as authors? 
        # Or just start processing sections from start_index
        extracted_data['Authors'] = ""
        current_index = start_index

    # --- 4. Extract Sections ---
    # Logic:
    # - Identify Headings (Standard or Dynamic)
    # - Copy content of "same size" until next heading
    
    standard_headings = [
        "Abstract", "Introduction", "Methodology", "Materials and Methods", 
        "Results", "Discussion", "Conclusion", "Conclusions", "References"
    ]
    
    current_section = None
    current_section_content = []
    current_section_font_size = None # To track "same size" logic
    
    while current_index < len(all_lines):
        line = all_lines[current_index]
        text = line['text'].strip()
        size = line['font_size']
        is_bold = line['is_bold']
        
        if not text:
            current_index += 1
            continue
            
        # Check if this line is a Heading
        is_heading = False
        heading_name = ""
        
        # A. Check Standard Headings
        # We check if the line matches the heading (case-insensitive, optional numbering/punctuation)
        for h in standard_headings:
            # Regex: Start of line, optional number (1. or 1), optional space, heading, optional punctuation (: or .), end of line
            # We use re.IGNORECASE
            pattern = rf"^(?:\d+\.?\s*)?{re.escape(h)}[:.]?$"
            if re.match(pattern, text, re.IGNORECASE):
                is_heading = True
                heading_name = h 
                break
        
        # B. Check Dynamic Headings
        # "Bold and dark ... but less than text size of title"
        if not is_heading:
            if is_bold and size < max_size:
                # Also check it's not just a bold word in a paragraph. 
                # Assume headings are short-ish lines.
                if len(text) < 100:
                    # Additional check: If we are already in a section, and the font size is the same as content,
                    # maybe it's just bold text in content?
                    # User said: "also it can be of same text size as content or some what bigger text"
                    # So bold content *could* be a heading.
                    # But usually headings are short.
                    # Let's assume if it's short and bold, it's a heading.
                    is_heading = True
                    heading_name = text # Use the line text as the heading
        
        if is_heading:
            # Save previous section
            if current_section:
                extracted_data[current_section] = "\n".join(current_section_content).strip()
            
            # Start new section
            current_section = heading_name
            current_section_content = []
            current_section_font_size = None # Reset expected font size
            
            # Move to next line (don't include heading in content)
            current_index += 1
            continue
            
        # If not a heading, it's content.
        # Logic: "copy all the text of same size"
        if current_section:
            # If we haven't established the section's font size yet, set it from the first content line
            if current_section_font_size is None:
                current_section_font_size = size
                current_section_content.append(text)
            else:
                # Check if size is "same" (allow small tolerance, e.g., 0.5 pt)
                if abs(size - current_section_font_size) < 1.0:
                    current_section_content.append(text)
                else:
                    # Text is different size. 
                    # User said "copy all the text of same size till introduction comes".
                    # This implies we SKIP text of different size? 
                    # Or maybe we stop? 
                    # "till introduction comes" implies we continue scanning for headings, 
                    # but maybe we just don't add this specific line to the content?
                    # Let's assume we skip it (e.g. it's a footnote or caption).
                    pass
        
        current_index += 1
        
    # Save the last section
    if current_section:
        extracted_data[current_section] = "\n".join(current_section_content).strip()

    return extracted_data

def process_line(chars):
    """
    Helper to process a list of characters into a line dict with metadata.
    """
    text = "".join([c['text'] for c in chars])
    
    # Determine font size (use mode or max? User said "largest size text", so max is good for title.
    # For body text, mode might be better, but max is usually fine for a single line.)
    sizes = [c['size'] for c in chars]
    font_size = max(sizes) if sizes else 0
    
    # Determine boldness
    # 'fontname' often contains 'Bold' or 'Bd'
    # Check if a significant portion of chars are bold
    bold_chars = [c for c in chars if 'Bold' in c.get('fontname', '') or 'Bd' in c.get('fontname', '')]
    is_bold = len(bold_chars) > len(chars) * 0.5 # If >50% chars are bold, line is bold
    
    return {
        'text': text,
        'font_size': font_size,
        'is_bold': is_bold
    }
