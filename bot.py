import subprocess
import json
from io import StringIO
from discord.utils import get
import os
import discord
from discord.ext import commands
from discord.ext.commands import has_role
from dotenv import load_dotenv
import subprocess
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="&", intents=intents)

activity_log = []

def log_activity(user, command):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {user} ejecutó: {command}"
    activity_log.append(entry)
    if len(activity_log) > 50:
        activity_log.pop(0)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# ────── Comandos para todos ──────

@bot.command()
async def players(ctx):
    result = send_rcon_command("list")
    if ":" in result:
        _, player_list = result.split(":", 1)
        player_list = player_list.strip()
        if player_list:
            await ctx.send(f"👥 Están conectados: {player_list}")
        else:
            await ctx.send("👥 No hay jugadores conectados.")
    else:
        await ctx.send("⚠️ No se pudoo obtener la lista de jugadores.")

@bot.command()
async def pingmc(ctx):
    result = send_rcon_command("list")
    if "There are" in result:
        await ctx.send("✅ Servidor activo.")
    else:
        await ctx.send("⚠️ No se pudo verificar el estado del servidor.")

@bot.command()
async def say(ctx, *, message):
    log_activity(ctx.author, f"&say {message}")
    mc_message = f"say [*] {ctx.author.display_name} dijo: {message}"
    try:
        subprocess.check_output(["tmux", "send-keys", "-t", "minecraft", mc_message, "C-m"])
        await ctx.send("✅ Mensaje enviado al servidor.")
    except Exception as e:
        await ctx.send(f"❌ Error enviando mensaje: {e}")

@bot.command()
async def hlp(ctx):
    user_roles = [r.name for r in ctx.author.roles]
    # Comandos accesibles para todos
    help_msg = (
        "**🔓 Comandos públicos:**\n"
        "`&hlp` → Muestra esta ayuda.\n"
        "`&players` → Jugadores conectados.\n"
        "`&pingmc` → Ping al servidor.\n"
        "`&say <mensaje>` → Mensaje en Minecraft.\n"
    )

    # Si el usuario tiene el rol "Acceso a Consola", añadimos lo demás
    if "Acceso a Consola" in user_roles:
        help_msg += (
            "\n**🔐 Comandos de consola (Acceso a Consola):**\n"
            "`&ram` → Uso de RAM.\n"
            "`&bateria` → Estado de bateria del servidor.\n"
            "`&issue <comando>` → Comando personalizado.\n"
            "`&log` → Últimas 10 líneas de consola.\n"
            "`&activitylog` → Historial de actividad.\n"
        )

    await ctx.send(help_msg)

# ────── Comandos con rol ──────

@bot.command()
@commands.has_role("Acceso a Consola")
async def bateria(ctx):
    try:
        result = subprocess.run(['termux-battery-status'], capture_output=True, text=True)
        data = json.loads(result.stdout)
        porcentaje = data["percentage"]
        estado = data["status"]
        await ctx.send(f"🔋 **Batería:** {porcentaje}% ({estado})")
    except Exception as e:
        await ctx.send("❌ Error al obtener el estado de la batería.")

@bot.command()
async def ram(ctx):
    """Muestra el uso de RAM"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    await ctx.send(
        f"🧠 RAM usada: {mem.used // 1024**2} MB / {mem.total // 1024**2} MB\n"
        f"📦 SWAP usada: {swap.used // 1024**2} MB / {swap.total // 1024**2} MB"
    )

@bot.command()
@has_role("Acceso a Consola")
async def issue(ctx, *, command):
    log_activity(ctx.author, f"&issue {command}")
    try:
        subprocess.check_output(["tmux", "send-keys", "-t", "minecraft", command, "C-m"])
        await ctx.send(f"🛠️ Comando enviado: `{command}`")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@has_role("Acceso a Consola")
async def log(ctx):
    log_activity(ctx.author, "&log")
    try:
        result = subprocess.check_output(["tmux", "capture-pane", "-pt", "minecraft", "-S", "-10"]).decode()
        file = discord.File(fp=StringIO(result), filename="log.txt")
        await ctx.send("📄 Últimas 10 líneas de consola:", file=file)
    except Exception as e:
        await ctx.send(f"❌ Error al leer el log: {e}")

@bot.command()
@has_role("Acceso a Consola")
async def activitylog(ctx):
    log_activity(ctx.author, "&activitylog")
    if not activity_log:
        await ctx.send("📭 No hay actividades registradas todavía.")
        return
    content = "\n".join(activity_log[-10:])
    await ctx.send(f"📘 Registro de actividad:\n```\n{content}```")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("🚫 No tienes el rol necesario para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Falta un argumento para este comando.")
    else:
        raise error

bot.run(TOKEN)
