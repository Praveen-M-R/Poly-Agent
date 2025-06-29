import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR:{BASE_DIR}")
# Load environment variables from .envvar file
load_dotenv(os.path.join(BASE_DIR, '.envvar'))

# Environment Variables
GIT_ACCESS_KEY = os.getenv('GIT_ACCESS_KEY')
ORGANIZATION = os.getenv('ORGANIZATION')
API_KEY = os.getenv('API_KEY')
