"""Apheris Foundry dashboard for the hackathon VM (no Foundry Hub here, so it wraps the docker commands)."""
import json, os, subprocess, time, shlex
from pathlib import Path
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
APHERIS = HERE.parent          # .../hackathon-team-3/apheris
RFD = APHERIS / "rfd4"
RUNS = RFD / "runs"
Q = "quay.io/apheris/oslo-hackathon"
WEIGHTS = ["her2-novel-2026-11-09", "her2-2026-11-07", "antibody-2026-10-30"]
FOLDERS = {"boltz2": "apheris-boltz-v1.3.0-boltz2"}
JOB = RUNS / ".gui_job.json"   # one heavy job at a time (single shared GPU)

st.set_page_config(page_title="Apheris Foundry (VM)", layout="wide")
st.title("Apheris Foundry: hackathon VM")

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def job_state():
    if not JOB.exists():
        return None
    j = json.loads(JOB.read_text())
    j["running"] = Path(f"/proc/{j['pid']}").exists()
    return j

def docker_prefix():
    uid, gid = os.getuid(), os.getgid()
    return (f"docker run --rm --gpus all --shm-size 16g --user {uid}:{gid} -e HOME=/tmp "
            f"-v /etc/passwd:/etc/passwd:ro -v {RFD}:/work -w /work")

tab_run, tab_runs, tab_sys, tab_docs = st.tabs(["Launch", "Runs", "GPU & containers", "Docs"])

with tab_run:
    j = job_state()
    if j and j["running"]:
        st.warning(f"Job running: {j['name']} (pid {j['pid']}). Wait for it to finish, the GPU is shared.")
    st.subheader("Design")
    c1, c2, c3, c4 = st.columns(4)
    weight = c1.selectbox("Weight", WEIGHTS)
    n = c2.number_input("Replicates", 1, 2000, 4)
    seed = c3.number_input("Seed", 0, 10**6, 1)
    name = c4.text_input("Run name", f"her2/{time.strftime('%m%d-%H%M')}")
    specs = sorted(str(p.relative_to(RFD)) for d in ("Data",) for p in (RFD / d).rglob("*") if p.suffix in (".yaml", ".json"))
    spec = st.selectbox("Spec file", specs, index=specs.index("Data/12-her2/her2_cdrh3.yaml") if "Data/12-her2/her2_cdrh3.yaml" in specs else 0)
    extra = st.text_input("Extra flags", "--recycle-strategy high/front_loaded")
    cmd = (f"{docker_prefix()} {Q}:apheris-rfd4-proteina-v0.3.0-{weight} module-run design "
           f"--input {spec} --output runs/{name}/design --num-replicates {n} --seed {seed} {extra}")
    st.code(cmd, language="bash")
    if st.button("Start design", type="primary", disabled=bool(j and j["running"])):
        out = RUNS / name
        out.mkdir(parents=True, exist_ok=True)
        log = out / "gui.log"
        (out / "command.txt").write_text(cmd + "\n")  # record every run (team rule)
        p = subprocess.Popen(f"cd {RFD} && {cmd}", shell=True, stdout=open(log, "w"), stderr=subprocess.STDOUT, start_new_session=True)
        JOB.write_text(json.dumps({"pid": p.pid, "name": name, "log": str(log)}))
        st.rerun()
    if j:
        st.subheader(f"Last job: {j['name']} ({'running' if j['running'] else 'finished'})")
        if j["running"] and st.button("Stop job"):
            subprocess.run(f"pkill -g {j['pid']}", shell=True)
        lp = Path(j["log"])
        st.code("\n".join(lp.read_text().splitlines()[-40:]) if lp.exists() else "", language="text")
        if j["running"]:
            time.sleep(5); st.rerun()

with tab_runs:
    metrics = sorted(RUNS.rglob("*metrics*.csv"))
    if not metrics:
        st.info("No metrics CSVs yet. Run a design first.")
    else:
        pick = st.selectbox("Metrics file", metrics, format_func=lambda p: str(p.relative_to(RUNS)))
        df = pd.read_csv(pick)
        st.caption(f"{len(df)} rows")
        num = df.select_dtypes("number").columns.tolist()
        if num:
            sortc = st.selectbox("Sort by", num, index=num.index("min_ipae") if "min_ipae" in num else 0)
            df = df.sort_values(sortc, ascending=(sortc == "min_ipae"))
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), pick.name)
    cifs = sorted(RUNS.rglob("*_generated.cif"))
    st.write(f"{len(cifs)} generated structures")
    if cifs:
        cif = st.selectbox("Structure", cifs, format_func=lambda p: str(p.relative_to(RUNS)))
        import py3Dmol  # noqa
        from stmol import showmol
        v = py3Dmol.view(width=800, height=500)
        v.addModel(cif.read_text(), "cif"); v.setStyle({"cartoon": {"color": "spectrum"}}); v.zoomTo()
        showmol(v, height=500, width=800)

with tab_sys:
    st.code(sh("nvidia-smi"), language="text")
    st.code(sh("docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'"), language="text")
    st.code(sh("df -h ~ | tail -1; free -h | head -2"), language="text")

with tab_docs:
    pages = sorted(RFD.glob("*.md"))
    p = st.selectbox("Page", pages, index=[x.name for x in pages].index("18-vm.md"), format_func=lambda p: p.name)
    st.markdown(p.read_text())
    for pdf in ("2026-11_Oslo_hackathon_Apheris_challenge.md", "ai-antibodies-hackathon-apheris.md"):
        with st.expander(pdf):
            st.markdown((APHERIS / "challenge" / pdf).read_text())
