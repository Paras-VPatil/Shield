import sys
import os

# Add the project root and backend folder to the path so that 'app.main' and other internal imports work.
# Vercel runs from the root, but our FastAPI source is in 'the_shield/backend'.
current_dir = os.path.dirname(__file__)
backend_dir = os.path.join(current_dir, "..", "the_shield", "backend")
sys.path.append(backend_dir)

# Now we can import the app instance from the backend
from app.main import app
