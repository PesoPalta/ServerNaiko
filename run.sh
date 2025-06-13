#!/data/data/com.termux/files/usr/bin/bash

# 🧹 (Opcional) Cierra todas las sesiones anteriores de tmux
tmux kill-server

# 📡 Inicia el túnel de Cloudflare en segundo plano
tmux new-session -d -s tunnel 'cloudflared tunnel run minecraft-tunnel'

# 🕹️ Inicia el servidor de Minecraft con Paper
tmux new-session -d -s minecraft 'java -Xms512M -Xmx3G -jar paper-1.21.4-224.jar nogui'

echo "✅ Túnel y servidor de Minecraft iniciados correctamente."
echo "🖥️ Puedes reconectarte con: tmux attach -t minecraft"
