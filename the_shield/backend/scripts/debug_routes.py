from app.main import app
for route in app.routes:
    # Handle Mount objects which don't have 'methods'
    methods = getattr(route, 'methods', None)
    path = getattr(route, 'path', 'Unknown')
    print(f"Path: {path} | Methods: {methods}")
