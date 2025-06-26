import cv2
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
import argparse
from typing import Optional, Dict, Any
import json


class PNGTextExtractor:
    """
    A comprehensive text extraction tool for PNG images using pytesseract.
    Includes image preprocessing options to improve OCR accuracy.
    """

    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the text extractor.

        Args:
            tesseract_path: Path to tesseract executable (if not in PATH)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            print(f"Error: Tesseract not found. Please install tesseract-ocr.")
            print(f"Details: {e}")

    def preprocess_image(self, image_path: str, preprocessing_options: Dict[str, Any]) -> Image.Image:
        """
        Preprocess the image to improve OCR accuracy.

        Args:
            image_path: Path to the PNG file
            preprocessing_options: Dictionary of preprocessing options

        Returns:
            Preprocessed PIL Image
        """
        # Load image
        img = Image.open(image_path)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Apply preprocessing based on options
        if preprocessing_options.get('grayscale', False):
            img = img.convert('L')

        if preprocessing_options.get('enhance_contrast', False):
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(preprocessing_options.get('contrast_factor', 2.0))

        if preprocessing_options.get('enhance_sharpness', False):
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(preprocessing_options.get('sharpness_factor', 2.0))

        if preprocessing_options.get('denoise', False):
            img = img.filter(ImageFilter.MedianFilter(size=3))

        if preprocessing_options.get('resize', False):
            scale_factor = preprocessing_options.get('scale_factor', 2.0)
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Advanced preprocessing with OpenCV
        if preprocessing_options.get('threshold', False):
            # Convert PIL to OpenCV format
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # Apply threshold
            threshold_type = preprocessing_options.get('threshold_type', 'adaptive')
            if threshold_type == 'adaptive':
                processed = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
            else:
                _, processed = cv2.threshold(
                    gray, preprocessing_options.get('threshold_value', 127),
                    255, cv2.THRESH_BINARY
                )

            # Convert back to PIL
            img = Image.fromarray(processed)

        if preprocessing_options.get('morphology', False):
            # Convert to OpenCV if not already
            if img.mode != 'L':
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            else:
                img_cv = np.array(img)

            # Apply morphological operations
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(img_cv, cv2.MORPH_CLOSE, kernel)
            img = Image.fromarray(processed)

        return img

    def extract_text_basic(self, image_path: str, language: str = 'eng') -> str:
        """
        Basic text extraction from PNG file.

        Args:
            image_path: Path to the PNG file
            language: Language for OCR (default: 'eng')

        Returns:
            Extracted text as string
        """
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=language)
            return text.strip()
        except Exception as e:
            return f"Error extracting text: {e}"

    def extract_text_advanced(self,
                              image_path: str,
                              language: str = 'eng',
                              config: str = '',
                              preprocessing_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Advanced text extraction with preprocessing and detailed output.

        Args:
            image_path: Path to the PNG file
            language: Language for OCR
            config: Custom tesseract configuration
            preprocessing_options: Image preprocessing options

        Returns:
            Dictionary containing extracted text and metadata
        """
        if preprocessing_options is None:
            preprocessing_options = {}

        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path, preprocessing_options)

            # Extract text
            text = pytesseract.image_to_string(processed_img, lang=language, config=config)

            # Get detailed data
            data = pytesseract.image_to_data(processed_img, lang=language, output_type=pytesseract.Output.DICT)

            # Get confidence scores
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Extract words with positions and confidence
            words_info = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    words_info.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })

            return {
                'extracted_text': text.strip(),
                'average_confidence': round(avg_confidence, 2),
                'word_count': len(text.split()),
                'character_count': len(text),
                'words_with_positions': words_info,
                'preprocessing_applied': preprocessing_options,
                'success': True
            }

        except Exception as e:
            return {
                'extracted_text': '',
                'error': str(e),
                'success': False
            }

    def extract_text_with_layout_analysis(self, image_path: str, language: str = 'eng') -> Dict[str, Any]:
        """
        Extract text with layout analysis (paragraphs, lines, words).

        Args:
            image_path: Path to the PNG file
            language: Language for OCR

        Returns:
            Dictionary with structured text extraction
        """
        try:
            img = Image.open(image_path)

            # Get layout analysis
            data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)

            # Organize by blocks, paragraphs, lines
            blocks = {}
            current_block = None
            current_paragraph = None
            current_line = None

            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    block_num = data['block_num'][i]
                    par_num = data['par_num'][i]
                    line_num = data['line_num'][i]

                    # Initialize block if new
                    if block_num not in blocks:
                        blocks[block_num] = {'paragraphs': {}}

                    # Initialize paragraph if new
                    if par_num not in blocks[block_num]['paragraphs']:
                        blocks[block_num]['paragraphs'][par_num] = {'lines': {}}

                    # Initialize line if new
                    if line_num not in blocks[block_num]['paragraphs'][par_num]['lines']:
                        blocks[block_num]['paragraphs'][par_num]['lines'][line_num] = {'words': []}

                    # Add word
                    blocks[block_num]['paragraphs'][par_num]['lines'][line_num]['words'].append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })

            # Compile full text
            full_text = pytesseract.image_to_string(img, lang=language)

            return {
                'full_text': full_text.strip(),
                'structured_layout': blocks,
                'success': True
            }

        except Exception as e:
            return {
                'full_text': '',
                'error': str(e),
                'success': False
            }

    def batch_extract(self, image_folder: str, output_file: str = 'extracted_texts.json') -> Dict[str, Any]:
        """
        Extract text from multiple PNG files in a folder.

        Args:
            image_folder: Path to folder containing PNG files
            output_file: Output JSON file name

        Returns:
            Dictionary with results for all images
        """
        results = {}
        png_files = [f for f in os.listdir(image_folder) if f.lower().endswith('.png')]

        for filename in png_files:
            file_path = os.path.join(image_folder, filename)
            print(f"Processing: {filename}")

            result = self.extract_text_advanced(file_path)
            results[filename] = result

        # Save results to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Extract text from PNG images using pytesseract')
    parser.add_argument('image_path', help='Path to PNG image file')
    parser.add_argument('--language', '-l', default='eng', help='Language for OCR (default: eng)')
    parser.add_argument('--preprocess', '-p', action='store_true', help='Apply preprocessing')
    parser.add_argument('--output', '-o', help='Output file for extracted text')
    parser.add_argument('--advanced', '-a', action='store_true', help='Use advanced extraction with details')

    args = parser.parse_args()

    # Initialize extractor
    extractor = PNGTextExtractor()

    # Set preprocessing options if requested
    preprocessing_options = {}
    if args.preprocess:
        preprocessing_options = {
            'grayscale': True,
            'enhance_contrast': True,
            'contrast_factor': 1.5,
            'resize': True,
            'scale_factor': 2.0,
            'threshold': True,
            'threshold_type': 'adaptive'
        }

    # Extract text
    if args.advanced:
        result = extractor.extract_text_advanced(
            args.image_path,
            args.language,
            preprocessing_options=preprocessing_options
        )
        print(f"Extracted Text:\n{result['extracted_text']}")
        print(f"Average Confidence: {result.get('average_confidence', 'N/A')}%")
        print(f"Word Count: {result.get('word_count', 'N/A')}")
    else:
        text = extractor.extract_text_basic(args.image_path, args.language)
        print(f"Extracted Text:\n{text}")

    # Save output if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            if args.advanced:
                json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                f.write(text)
        print(f"Output saved to: {args.output}")


# Example usage
if __name__ == "__main__":
    # Demo usage (comment out main() to run demo)
    print("PNG Text Extractor Demo")
    print("=" * 50)

    # Example usage
    extractor = PNGTextExtractor()

    # Example 1: Basic extraction
    print("\nExample 1: Basic text extraction")
    print("extractor.extract_text_basic('your_image.png')")

    # Example 2: Advanced extraction with preprocessing
    print("\nExample 2: Advanced extraction with preprocessing")
    preprocessing_opts = {
        'grayscale': True,
        'enhance_contrast': True,
        'contrast_factor': 1.5,
        'resize': True,
        'scale_factor': 2.0,
        'threshold': True
    }
    print("result = extractor.extract_text_advanced('your_image.png', preprocessing_options=preprocessing_opts)")
    result = extractor.extract_text_basic('/Users/soumya/Downloads/b.png')
    print(result)
    # Example 3: Batch processing
    # print("\nExample 3: Batch processing")
    # print("extractor.batch_extract('path/to/image/folder')")
    #
    # print("\nTo use with command line:")
    # print("python script.py image.png --advanced --preprocess --output result.json")

    # Uncomment the next line to use command line interface
    # main()