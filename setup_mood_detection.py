import os
import sys
import urllib.request
import bz2
import shutil
import subprocess

def install_requirements():
    """Install required Python packages."""
    requirements = [
        'dlib',
        'scipy',
        'numpy',
        'opencv-python'
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
            return False
    return True

def download_predictor():
    """Download and extract the facial landmark predictor model."""
    predictor_path = 'mood_detection/shape_predictor_68_face_landmarks.dat'
    
    # Skip if file already exists
    if os.path.exists(predictor_path):
        print("Facial landmark predictor model already exists.")
        return True
    
    print("Downloading facial landmark predictor model...")
    url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
    bz2_path = predictor_path + '.bz2'
    
    try:
        # Create mood_detection directory if it doesn't exist
        os.makedirs('mood_detection', exist_ok=True)
        
        # Download the file
        urllib.request.urlretrieve(url, bz2_path)
        
        # Extract the file
        with bz2.BZ2File(bz2_path) as fr, open(predictor_path, 'wb') as fw:
            shutil.copyfileobj(fr, fw)
        
        # Remove the compressed file
        os.remove(bz2_path)
        print("Successfully downloaded and extracted the model.")
        return True
    except Exception as e:
        print(f"Error downloading predictor model: {str(e)}")
        return False

def main():
    """Main setup function."""
    print("Setting up mood detection requirements...")
    
    if not install_requirements():
        print("Failed to install required packages.")
        return
    
    if not download_predictor():
        print("Failed to download facial landmark predictor model.")
        return
    
    print("\nSetup completed successfully!")
    print("You can now use the enhanced mood detection features.")

if __name__ == "__main__":
    main() 