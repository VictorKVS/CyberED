"""CyberED local static server + Silero TTS gateway (Python 3.10+).

Usage:
  python cybered_tts_server.py --site "G:\\1\\CyberED-Stage1\\docs\\osi\\stage1" --port 8088
  python cybered_tts_server.py --site "..." --silero-model "G:\\1\\FATHER-TTS\\silero\\model.pt"
Dependencies: pip install torch (only for Silero synthesis).
Models are NEVER downloaded automatically. Never expose this server to the internet.
"""
import argparse
import io
import json
import logging
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import wave

LOG = logging.getLogger("fas.tts")
VOICES = ("xenia", "baya", "kseniya", "aidar", "eugene")
MODEL = None
MODEL_LOCK = threading.Lock()


def load_model(path):
    global MODEL
    if not path:
        LOG.warning("Silero model path not configured; API will return 503")
        return
    model_file = Path(path)
    if not model_file.is_file():
        LOG.error("Model not found: %s", model_file)
        return
    try:
        import torch
        MODEL = torch.package.PackageImporter(str(model_file)).load_pickle("tts_models", "model")
        MODEL.to(torch.device("cpu"))
        LOG.info("Silero model loaded: %s", model_file)
    except Exception:
        LOG.exception("Failed to load Silero model")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        LOG.info("http client=%s " + fmt, self.client_address[0], *args)

    def send_json(self, status, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/tts/health":
            self.send_json(200, {"provider": "silero", "ready": MODEL is not None,
                                 "voices": list(VOICES), "model_configured": bool(self.server.model_path)})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/tts/local":
            self.send_json(404, {"error": "Unknown API route"})
            return
        LOG.info("tts request received")
        if MODEL is None:
            self.send_json(503, {"error": "Silero model not loaded", "hint": "Start server with --silero-model pointing to an installed compatible Silero v5 model"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 32768:
                self.send_json(413, {"error": "Request body must be 1..32768 bytes"})
                return
            req = json.loads(self.rfile.read(length))
            phrase = req.get("text")
            speaker = req.get("voice", "xenia")
            if not isinstance(phrase, str) or not phrase.strip() or len(phrase) > 2000:
                self.send_json(400, {"error": "Invalid text"})
                return
            if speaker not in VOICES:
                self.send_json(400, {"error": "Unsupported voice"})
                return
            import torch
            with MODEL_LOCK, torch.inference_mode():
                audio = MODEL.apply_tts(text=phrase, speaker=speaker, sample_rate=48000)
            samples = audio.detach().cpu().numpy()
            import array
            pcm = array.array("h", (max(-32768, min(32767, int(float(v) * 32767))) for v in samples))
            stream = io.BytesIO()
            with wave.open(stream, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(pcm.tobytes())
            payload = stream.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            LOG.info("tts success voice=%s chars=%d bytes=%d", speaker, len(phrase), len(payload))
        except Exception:
            LOG.exception("tts synthesis failed")
            self.send_json(500, {"error": "TTS synthesis failed; see server log"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--port", type=int, default=8088)
    parser.add_argument("--silero-model", default=os.environ.get("SILERO_MODEL", ""))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    site = Path(args.site).resolve()
    if not site.is_dir():
        parser.error("Site directory not found: " + str(site))
    load_model(args.silero_model)
    from functools import partial
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(site)))
    server.model_path = args.silero_model
    LOG.info("Serving http://127.0.0.1:%d/avatar-lab.html; ready=%s", args.port, MODEL is not None)
    server.serve_forever()


if __name__ == "__main__":
    main()
