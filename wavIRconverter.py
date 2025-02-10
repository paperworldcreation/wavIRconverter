import gradio as gr
import numpy as np
import soundfile as sf
import logging
from pathlib import Path
import wave

def get_wav_info(file_path: str) -> dict:
    """
    Get detailed WAV file information including exact bit depth.
    """
    info = sf.info(file_path)
    
    # Get bit depth from soundfile format
    format_to_bits = {
        'PCM_S8': 8,
        'PCM_16': 16,
        'PCM_24': 24,
        'PCM_32': 32,
        'FLOAT': 32,
        'DOUBLE': 64
    }
    
    bit_depth = format_to_bits.get(info.subtype, 16)  # Default to 16 if unknown
    
    return {
        'bit_depth': bit_depth,
        'sample_rate': info.samplerate,
        'channels': info.channels,
        'format': info.subtype
    }

def process_wav_file(input_path: str) -> tuple:
    """
    Read a WAV file and return its data and properties.
    """
    try:
        # Get file information
        info = get_wav_info(input_path)
        
        # Read the audio data
        data, sample_rate = sf.read(input_path)
        
        # Ensure data is in correct range
        if data.dtype in [np.float32, np.float64]:
            data = np.clip(data, -1.0, 1.0)
        
        return data, info
    except Exception as e:
        logging.error(f"Error processing file {input_path}: {str(e)}")
        raise gr.Error(f"Error processing file: {str(e)}")

def save_wav_file(data: np.ndarray, info: dict, output_path: str) -> None:
    """
    Save audio data as a WAV file with exactly matching properties.
    """
    try:
        # Map bit depth to soundfile subtype
        bits_to_subtype = {
            8: 'PCM_S8',
            16: 'PCM_16',
            24: 'PCM_24',
            32: 'PCM_32' if info['format'] != 'FLOAT' else 'FLOAT',
            64: 'DOUBLE'
        }
        
        # Get the appropriate subtype
        subtype = bits_to_subtype.get(info['bit_depth'], info['format'])
        
        # Save with exact specifications
        sf.write(
            output_path,
            data,
            info['sample_rate'],
            subtype=subtype
        )
            
    except Exception as e:
        logging.error(f"Error saving file {output_path}: {str(e)}")
        raise gr.Error(f"Error saving file: {str(e)}")

def convert_wav_files(files) -> list:
    """
    Convert uploaded WAV files while preserving exact properties.
    """
    if not files:
        raise gr.Error("Please upload at least one file")
    
    output_files = []
    conversion_info = []
    
    for file in files:
        try:
            input_path = Path(file.name)
            output_path = input_path.parent / f"converted_{input_path.name}"
            
            # Get data and specifications
            data, info = process_wav_file(str(input_path))
            
            # Save with matching specifications
            save_wav_file(data, info, str(output_path))
            
            # Store conversion info
            conversion_info.append({
                'filename': input_path.name,
                'info': info
            })
            
            output_files.append(str(output_path))
            
        except Exception as e:
            logging.error(f"Error processing {input_path.name}: {str(e)}")
            raise gr.Error(f"Error processing {input_path.name}: {str(e)}")
    
    return output_files, conversion_info

# Create Gradio interface
with gr.Blocks() as iface:
    gr.Markdown("# WAV File Converter")
    gr.Markdown("""
    Upload one or more WAV files to convert them while preserving:
    - Original sample rate
    - Original bit depth
    - Original number of channels
    - All audio samples (no data loss)
    
    Supports PCM (8-bit to 32-bit) and Float formats.
    """)
    
    with gr.Row():
        input_files = gr.File(
            file_count="multiple",
            label="Input WAV Files"
        )
    
    with gr.Row():
        convert_btn = gr.Button("Convert Files")
        
    with gr.Row():
        info_box = gr.Textbox(
            label="Conversion Info",
            interactive=False
        )
    
    with gr.Row():
        output_files = gr.File(
            file_count="multiple",
            label="Converted Files"
        )
    
    def convert_and_show_info(files):
        converted_files, conversion_info = convert_wav_files(files)
        
        # Generate info text
        info_text = "Conversion completed successfully!\n"
        for item in conversion_info:
            info_text += f"\n{item['filename']}:\n"
            info_text += f"- Bit Depth: {item['info']['bit_depth']}-bit\n"
            info_text += f"- Sample Rate: {item['info']['sample_rate']}Hz\n"
            info_text += f"- Channels: {item['info']['channels']}\n"
            info_text += f"- Format: {item['info']['format']}\n"
        
        return converted_files, info_text
    
    convert_btn.click(
        fn=convert_and_show_info,
        inputs=[input_files],
        outputs=[output_files, info_box]
    )

# Launch the interface
if __name__ == "__main__":
    iface.launch()