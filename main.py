from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import uuid, threading, time, os

app = FastAPI()
jobs = {}

os.makedirs("outputs", exist_ok=True)

def run_job(job_id, image, p1, p2):
    time.sleep(300)  # simulate long processing

    svg = f"""
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <text x="10" y="100">
        p1={p1}, p2={p2}
      </text>
    </svg>
    """

    path = f"outputs/{job_id}.svg"
    with open(path, "w") as f:
        f.write(svg)

    jobs[job_id]["status"] = "done"
    jobs[job_id]["path"] = path

@app.post("/start")
async def start(
    image: UploadFile = File(...),
    p1: int = Form(...),
    p2: int = Form(...)
):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}

    threading.Thread(
        target=run_job,
        args=(job_id, image, p1, p2)
    ).start()

    return {"job_id": job_id}

@app.get("/result/{job_id}")
def result(job_id: str):
    job = jobs.get(job_id)

    if not job:
        return JSONResponse({"message": "Invalid job"}, status_code=404)

    if job["status"] != "done":
        return JSONResponse(
            {"message": "Please wait more…"},
            status_code=202
        )

    return FileResponse(
        job["path"],
        media_type="image/svg+xml",
        filename="output.svg"
    )
