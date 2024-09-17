# pdf_reader.py

from PyPDF2 import PdfReader

def read_pdf_content(pdf_path):
    """
    Reads the content of a PDF and prints it for inspection.
    This will help us understand how the data is structured within the PDF.
    
    :param pdf_path: Path to the PDF file.
    :return: The extracted text from the PDF.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page_number, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text
                print(f"--- Page {page_number + 1} ---\n{page_text}\n{'='*50}")
            else:
                print(f"--- Page {page_number + 1} ---\nNo text extracted\n{'='*50}")
        
        # Return the full extracted text
        print(f"Full Extracted Text from {pdf_path}:\n{text}\n{'='*50}")
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Replace with the path to your sample PDF file
    pdf_path = "./Inspection 84292.pdf"
    read_pdf_content(pdf_path)
