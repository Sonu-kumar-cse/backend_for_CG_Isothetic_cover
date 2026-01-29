import os
import uuid
import time
import threading

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(__file__)
INPUT_DIR = os.path.join(BASE_DIR, "jobs", "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "jobs", "outputs")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- APP ----------------
app = FastAPI()

# CORS → required for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# job_id -> status
jobs = {}  # "running" | "done"

# ---------------- START PROCESS ----------------
@app.post("/start")
async def start_processing(
    image: UploadFile,
    p1: int = Form(...),
    p2: int = Form(...)
):
    job_id = str(uuid.uuid4())
    jobs[job_id] = "running"

    input_path = os.path.join(INPUT_DIR, f"{job_id}.png")
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.svg")

    # save image
    with open(input_path, "wb") as f:
        f.write(await image.read())

    # background task
    def process():
        # 🔁 simulate long processing
        time.sleep(10)

        # 🔽 replace this with YOUR real algorithm
        svg = f"""
        <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
          <rect x="10" y="10" width="380" height="180"
                fill="none" stroke="black" stroke-width="2"/>
          <text x="40" y="110" font-size="18">
            p1 = {p1}, p2 = {p2}
          </text>
        </svg>
        """

        with open(output_path, "w") as f:
            f.write(svg)

        jobs[job_id] = "done"

    threading.Thread(target=process).start()

    # ⬅️ immediate response
    return {"job_id": job_id}

# ---------------- GET RESULT ----------------
@app.get("/result/{job_id}")
def get_result(job_id: str):
    if job_id not in jobs:
        return JSONResponse(
            {"message": "Invalid job id"},
            status_code=404
        )

    if jobs[job_id] != "done":
        return JSONResponse(
            {"message": "Still processing, please wait"},
            status_code=202
        )

    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.svg")

    return FileResponse(
        output_path,
        media_type="image/svg+xml",
        filename="output.svg"
    )
