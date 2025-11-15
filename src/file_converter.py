"""
Module to handle audio conversion using ffmpeg
"""

import subprocess
import os


class FileConverter:
    """
    Interface for converting audio files using ffmpeg
    """
    
    @staticmethod
    def convert_to_format(input_path, output_path, output_format='mp3', quality='192k'):
        """
        Convert an audio file to a specified format
        
        Args:
            input_path (str): Path to the input audio file
            output_path (str): Path where the converted file should be saved
            output_format (str): Target audio format (mp3, wav, flac, etc.)
            quality (str): Audio quality (e.g., '192k', '256k', '320k')
        """
        try:
            # Build the ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ab', quality,  # Set audio bitrate
                '-ac', '2',      # Set audio channels to stereo
                '-ar', '44100',  # Set audio sample rate
                '-y',            # Overwrite output file if it exists
                output_path
            ]
            
            # Run the command
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg conversion failed: {result.stderr}")
                
            # Remove the original file after successful conversion
            if os.path.exists(input_path) and input_path != output_path:
                os.remove(input_path)
                
        except Exception as e:
            raise Exception(f"Error during audio conversion: {e}")
    
    @staticmethod
    def get_format_extension(audio_format):
        """
        Get the file extension for an audio format
        
        Args:
            audio_format (str): Audio format (mp3, wav, flac, etc.)
            
        Returns:
            str: File extension with dot (e.g., '.mp3')
        """
        format_map = {
            'mp3': '.mp3',
            'wav': '.wav',
            'flac': '.flac',
            'm4a': '.m4a',
            'aac': '.aac'
        }
        return format_map.get(audio_format.lower(), '.mp3')  # Default to mp3