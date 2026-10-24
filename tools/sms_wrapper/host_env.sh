# Source explicitly in the current shell. Does not edit ~/.profile or /etc.
smsforge_env_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PATH="$smsforge_env_root/out/host-bootstrap/venv/bin:$smsforge_env_root/sdk/sdcc-portable/bin:$smsforge_env_root/sdk/devkitSMS/tools:$PATH"
export SMS_DEVKITSMS="$smsforge_env_root/sdk/devkitSMS"
export PYTHONPATH="$smsforge_env_root/tools/sms_wrapper${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
unset smsforge_env_root
