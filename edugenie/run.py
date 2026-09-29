import os
import uvicorn
from dotenv import load_dotenv

# Ensure KMP duplicate library issue does not interrupt Windows runtime
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"[*] Starting EduGenie on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
