"""
Translation Module
Uses OpenAI API to translate English text to Lebanese Arabic with dialect-aware prompting
"""

import logging
import pandas as pd
import time
from pathlib import Path
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


def run(input_csv, output_csv):
    """
    Translate English transcript to Lebanese Arabic
    
    Args:
        input_csv (Path): Path to input CSV file with English transcript
        output_csv (Path): Path to output CSV file with Arabic translation
    """
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)
    
    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    
    # Create output directory if it doesn't exist
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Import config here to avoid circular imports
    from config import OPENAI_API_KEY, OPENAI_MODEL, TRANSLATION_TEMPERATURE
    
    if OPENAI_API_KEY == "your-openai-key-here":
        logger.error("OpenAI API key not set")
        raise ValueError("OpenAI API key not configured")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Load transcript
    logger.info(f"Loading transcript from: {input_csv}")
    df = pd.read_csv(input_csv)
    
    required_columns = ['start_sec', 'end_sec', 'speaker', 'text']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {required_columns}")
    
    logger.info(f"Found {len(df)} segments to translate")
    
    # Prepare rows for translation
    translated_rows = []
    
    # System prompt for Lebanese Arabic translation
    system_prompt = """You are a professional translator specializing in Lebanese Arabic dialect. 
    
    Your task is to translate English text to colloquial Lebanese Arabic while:
    1. Preserving the original meaning and humor
    2. Using authentic Lebanese dialect expressions
    3. Maintaining the speaking style and personality of the character
    4. Keeping the translation concise to fit the original audio timing
    5. Using Arabic script (not Latin transliteration)
    
    For South Park characters, maintain their distinctive speech patterns:
    - Stan: Normal, relatable teenager
    - Kyle: Intelligent, sometimes preachy
    - Cartman: Arrogant, manipulative, uses exaggerated expressions
    - Kenny: Muffled speech (when audible)
    - Randy: Adult, often excited or dramatic
    
    Translate naturally as if a Lebanese person is speaking, not a formal translation."""
    
    for index, row in df.iterrows():
        try:
            # Calculate segment duration for timing context
            duration = float(row['end_sec']) - float(row['start_sec'])
            
            # Create user prompt with context
            user_prompt = f"""Translate this English text to Lebanese Arabic:
            
            Text: "{row['text']}"
            Speaker: {row['speaker']}
            Duration: {duration:.1f} seconds
            
            Return only the Arabic translation, no explanations."""
            
            logger.info(f"Translating segment {index + 1}/{len(df)}: {row['text'][:50]}...")
            
            # Make API call
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TRANSLATION_TEMPERATURE,
                max_tokens=200
            )
            
            # Extract translation
            translation = response.choices[0].message.content.strip()
            
            # Clean up translation (remove quotes if present)
            translation = translation.strip('"\'')
            
            # Create new row with translation
            new_row = row.copy()
            new_row['text_ar'] = translation
            new_row['text_en'] = row['text']  # Keep original English
            
            translated_rows.append(new_row)
            
            logger.info(f"✅ Translated: {translation[:50]}...")
            
            # Rate limiting - be respectful to OpenAI API
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Failed to translate segment {index + 1}: {e}")
            
            # Add row with error placeholder
            new_row = row.copy()
            new_row['text_ar'] = f"[TRANSLATION ERROR: {row['text']}]"
            new_row['text_en'] = row['text']
            
            translated_rows.append(new_row)
            
            # Continue with next segment
            continue
    
    # Create DataFrame with translations
    df_translated = pd.DataFrame(translated_rows)
    
    # Reorder columns
    column_order = ['start_sec', 'end_sec', 'speaker', 'text_en', 'text_ar']
    df_translated = df_translated[column_order]
    
    # Save to CSV
    df_translated.to_csv(output_csv, index=False)
    
    logger.info(f"✅ Translation completed and saved to: {output_csv}")
    
    # Log statistics
    successful_translations = len(df_translated[~df_translated['text_ar'].str.contains('TRANSLATION ERROR', na=False)])
    logger.info(f"Successfully translated: {successful_translations}/{len(df_translated)} segments")
    
    if successful_translations < len(df_translated):
        logger.warning(f"Failed to translate {len(df_translated) - successful_translations} segments")


def check_openai_api():
    """Check if OpenAI API is available and configured"""
    try:
        from config import OPENAI_API_KEY
        
        if OPENAI_API_KEY == "your-openai-key-here":
            return False
        
        # Test API connection
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        return True
        
    except Exception as e:
        logger.error(f"OpenAI API check failed: {e}")
        return False


def validate_translation(csv_path):
    """
    Validate the generated translation CSV
    
    Args:
        csv_path (Path): Path to CSV file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Check required columns
        required_columns = ['start_sec', 'end_sec', 'speaker', 'text_en', 'text_ar']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns: {required_columns}")
            return False
        
        # Check for empty translations
        empty_translations = df['text_ar'].str.len() == 0
        if empty_translations.any():
            logger.warning(f"Found {empty_translations.sum()} empty translations")
        
        # Check for error translations
        error_translations = df['text_ar'].str.contains('TRANSLATION ERROR', na=False)
        if error_translations.any():
            logger.warning(f"Found {error_translations.sum()} translation errors")
        
        # Check Arabic text (should contain Arabic characters)
        has_arabic = df['text_ar'].str.contains('[\u0600-\u06FF]', na=False, regex=True)
        if not has_arabic.any():
            logger.warning("No Arabic characters found in translations")
        
        logger.info("✅ Translation validation completed")
        return True
        
    except Exception as e:
        logger.error(f"Translation validation failed: {e}")
        return False


def preview_translation(csv_path, num_samples=5):
    """
    Preview some translation samples
    
    Args:
        csv_path (Path): Path to CSV file
        num_samples (int): Number of samples to show
    """
    try:
        df = pd.read_csv(csv_path)
        
        logger.info(f"Translation Preview ({num_samples} samples):")
        logger.info("=" * 60)
        
        for i, row in df.head(num_samples).iterrows():
            logger.info(f"Speaker: {row['speaker']}")
            logger.info(f"English: {row['text_en']}")
            logger.info(f"Arabic: {row['text_ar']}")
            logger.info(f"Time: {row['start_sec']:.1f}s - {row['end_sec']:.1f}s")
            logger.info("-" * 40)
            
    except Exception as e:
        logger.error(f"Preview failed: {e}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) not in [3, 4]:
        print("Usage: python translate.py <input.csv> <output.csv> [preview]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    show_preview = len(sys.argv) == 4 and sys.argv[3] == "preview"
    
    logging.basicConfig(level=logging.INFO)
    
    if not check_openai_api():
        logger.error("OpenAI API not available or not configured")
        sys.exit(1)
    
    try:
        run(input_file, output_file)
        
        # Validate output
        if validate_translation(output_file):
            print("✅ Translation completed successfully")
            
            if show_preview:
                preview_translation(output_file)
        else:
            print("⚠️ Translation completed but validation failed")
            
    except Exception as e:
        logger.error(f"❌ Translation failed: {e}")
        sys.exit(1) 