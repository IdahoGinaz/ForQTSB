from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fitparse import FitFile
import zipfile, io, os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()  # ✅ This must come first

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your GitHub Pages domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_fit_from_zip(fobj):
    z = zipfile.ZipFile(fobj)
    for name in z.namelist():
        if name.lower().endswith('.fit'):
            return io.BytesIO(z.read(name))
    return None

def parse_vo2_from_fit_bytes(data_bytes):
    ff = FitFile(io.BytesIO(data_bytes))
    vo_val = None
    for msg in ff.get_messages():
        try:
            for field in msg:
                fdn = getattr(field, 'field_definition_number', None)
                fname = getattr(field, 'name', None)
                if fdn == 7 or (isinstance(fname, str) and fname.lower() in ('unknown_7', 'unknown 7', 'unknown-7')):
                    vo_val = field.value
                    break
            if vo_val is not None:
                break
        except Exception:
            continue
    return vo_val

@app.get("/")
async def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse({"error": "no filename"}, status_code=400)

    data = await file.read()
    fit_bytes = None

    if file.filename.lower().endswith(".zip"):
        fit_stream = extract_fit_from_zip(io.BytesIO(data))
        if not fit_stream:
            return JSONResponse({"error": "no .fit inside zip"}, status_code=400)
        fit_bytes = fit_stream.read()
    elif file.filename.lower().endswith(".fit"):
        fit_bytes = data
    else:
        return JSONResponse({"error": "unsupported file type"}, status_code=400)

    try:
        vo_raw = parse_vo2_from_fit_bytes(fit_bytes)
    except Exception as e:
        return JSONResponse({"error": "parse_failed", "message": str(e)}, status_code=500)

    if vo_raw is None:
        return JSONResponse({"found": False, "message": "VO2 field not found"}, status_code=200)

    try:
        vo2 = (float(vo_raw) * 3.5) / 65536
    except Exception:
        return JSONResponse({"error": "invalid_vo_value", "raw": vo_raw}, status_code=500)

    return JSONResponse({"found": True, "vo2": round(vo2, 3), "raw": vo_raw}, status_code=200)
