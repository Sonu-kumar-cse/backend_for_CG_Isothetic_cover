from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import threading
import time
import os

app = FastAPI()

# ---------------- CORS (IMPORTANT FIX) ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # allow GitHub Pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- STORAGE ----------------
jobs = {}
os.makedirs("outputs", exist_ok=True)

# ---------------- BACKGROUND JOB ----------------
def run_job(job_id: str, p1: int, p2: int):
    try:
        # simulate long processing
        time.sleep(300)  # 5 minutes

        # generate SVG output
        svg_content = f"""
        <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="white"/>
            <text x="20" y="100" font-size="18">
                p1 = {p1}, p2 = {p2}
            </text>
        </svg>
        """

        output_path = f"outputs/{job_id}.svg"
        with open(output_path, "w") as f:
            f.write(svg_content)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["path"] = output_path

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

# ---------------- API ENDPOINTS ----------------

@app.post("/start")
async def start_processing(
    image: UploadFile = File(...),
    p1: int = Form(...),
    p2: int = Form(...)
):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "processing"
    }

    threading.Thread(
        target=run_job,
        args=(job_id, p1, p2),
        daemon=True
    ).start()

    return {"job_id": job_id}


@app.get("/result/{job_id}")
def get_result(job_id: str):
    job = jobs.get(job_id)

    if not job:
        return JSONResponse(
            {"message": "Invalid job id"},
            status_code=404
        )

    if job["status"] == "processing":
        return JSONResponse(
            {"message": "Please wait more…"},
            status_code=202
        )

    if job["status"] == "error":
        return JSONResponse(
            {"message": "Processing failed", "error": job.get("error")},
            status_code=500
        )

    return FileResponse(
        job["path"],
        media_type="image/svg+xml",
        filename="output.svg"
    )
