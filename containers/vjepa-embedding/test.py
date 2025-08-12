import sys, time, math, torch, cv2, numpy as np
from transformers import AutoVideoProcessor, AutoModel

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <video_path> <output_npy>")
    sys.exit(1)

video_path, out_path = sys.argv[1], sys.argv[2]
frames_per_clip = 16
model_id = "facebook/vjepa2-vitl-fpc64-256"

device = torch.device("cpu")  # Docker on Mac = CPU-only
model = AutoModel.from_pretrained(model_id, torch_dtype=torch.float32).to(device).eval()
try:
    model.set_attn_implementation("eager")
except Exception:
    pass
processor = AutoVideoProcessor.from_pretrained(model_id)

cap = cv2.VideoCapture(video_path)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
idxs = [math.floor(i * total / frames_per_clip) for i in range(frames_per_clip)] if total else list(range(frames_per_clip))
frames=[]
for idx in idxs:
    if total: cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    if not ok: break
    frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
cap.release()
if not frames: raise RuntimeError("No frames read")

inputs = processor(videos=[frames], return_tensors="pt")
inputs = {k: v.to(device=device, dtype=torch.float32) for k, v in inputs.items()}

with torch.no_grad():
    _ = model(**inputs)
    t0 = time.perf_counter()
    out = model(**inputs)
    dt = time.perf_counter() - t0

emb = out.last_hidden_state.mean(dim=1).detach().cpu().numpy()[0].astype("float32")
np.save(out_path, emb)
print(f"[ok] wrote {out_path} | dim={emb.shape[0]} | frames={len(frames)} | time={dt*1000:.1f}ms")
