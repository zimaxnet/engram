import sys
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

try:
    import google.generativeai as genai
    print("✅ Successfully imported google.generativeai")
except ImportError as e:
    print(f"❌ Failed to import google.generativeai: {e}")

try:
    from google import genai
    print("✅ Successfully imported google.genai")
except ImportError as e:
    print(f"❌ Failed to import google.genai: {e}")

import pkg_resources
try:
    dist = pkg_resources.get_distribution("google-generativeai")
    print(f"google-generativeai version: {dist.version}")
except pkg_resources.DistributionNotFound:
    print("❌ google-generativeai not found via pkg_resources")
