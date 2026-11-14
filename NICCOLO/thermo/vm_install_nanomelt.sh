#!/bin/bash
# Install NanoMelt on the hackathon VM, inside ~/nick-work (shared machine: stay in your own folder).
set -euo pipefail
cd ~/nick-work
export MAMBA_ROOT_PREFIX=$HOME/nick-work/mamba
if [ ! -x bin/micromamba ]; then
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
fi
MM=$HOME/nick-work/bin/micromamba
if [ ! -d nmenv ]; then
  $MM create -y -q -p $HOME/nick-work/nmenv -c conda-forge -c bioconda \
      python=3.12 anarci hmmer biopython pip
fi
PY=$HOME/nick-work/nmenv/bin/python
$PY -m pip install -q --upgrade pip
$PY -m pip install -q nanomelt
echo "--- versions ---"
$PY -c "import torch, nanomelt; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
$PY -c "import anarci; print('anarci ok')"
echo "INSTALL_OK"
