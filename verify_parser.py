import parser
import os

def test_parser():
    if not os.path.exists("test_paper.pdf"):
        print("test_paper.pdf not found.")
        return

    with open("test_paper.pdf", "rb") as f:
        data = parser.parse_pdf(f)
    
    print("Extracted Data:")
    for key, value in data.items():
        print(f"{key}: {value[:50]}...") # Print first 50 chars

    # Assertions
    assert "A Novel Approach" in data["Title"]
    assert "John Doe" in data["Authors"]
    assert "This is the abstract" in data["Abstract"]
    assert "This is the introduction" in data["Introduction"]
    
    print("\nSUCCESS: All sections extracted correctly!")

if __name__ == "__main__":
    test_parser()
