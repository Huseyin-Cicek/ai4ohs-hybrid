@echo off
cd /d "C:\vscode-projects\llama.cpp"
start "" "C:\vscode-projects\llama.cpp\build\bin\Release\llama-server.exe" ^
  --model "models\Llama-3.2-3B-Instruct-Q4_K_M.gguf" ^
  --port 8080 ^
  --ctx-size 4096 ^
  --threads 8 ^
  --n-gpu-layers 999 ^
  --flash-attn auto ^
  --tensor-split 1.0
