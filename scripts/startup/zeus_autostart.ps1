$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repo
python scripts/dev/zeus_prompt_listener.py
