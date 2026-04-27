# LocalFlow

Local speech-to-text with GPU transcription and LLM refinement. Runs as a system tray app — press a hotkey, speak, and get refined text injected into any focused window.

## How It Works

1. **Record** — Click the tray icon or use the popup to start recording
2. **Transcribe** — Audio is transcribed locally using Faster Whisper on your GPU
3. **Refine** — The raw transcription is sent to an LLM (OpenAI or local Ollama) for refinement based on the selected mode
4. **Inject** — The refined text is copied to clipboard and typed into the active window via `xdotool`

## Modes

| Mode | Description |
|------|-------------|
| **Transcript** | Raw speech-to-text output, no LLM processing |
| **Prompt** | Converts spoken ramblings into clean, structured LLM prompts |
| **Code** | Generates code from spoken descriptions |
| **Enhancement** | Improves vocabulary, grammar, and fluency while preserving meaning |
| **Exaggeration** | Amplifies and dramatizes everything you said |
| **Interact** | General AI assistant — asks and answers questions via voice |
| **Fitness** | Voice-controlled food tracking — logs meals and macros to a local fitness API |
| **Todo** | Voice-controlled task management — create, list, complete, edit, and delete tasks via a local tasks API |

## Requirements

- Python 3.11+
- NVIDIA GPU with CUDA (for Whisper transcription)
- Linux with X11 (uses `xdotool` for text injection)
- `libportaudio2` (for audio recording)

## Setup

```bash
# Clone and enter the project
git clone <repo-url>
cd LocalFlow

# Run the setup script (installs system + Python deps)
./setup.sh

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings (API keys, model preferences, etc.)
```

## Configuration

Copy `.env.example` to `.env` and adjust:

```bash
# LLM backend — set USE_LOCAL=true for Ollama, false for OpenAI
USE_LOCAL=false
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini

# Local Ollama (when USE_LOCAL=true)
OLLAMA_MODEL=mistral:7b
OLLAMA_URL=http://localhost:11434

# Whisper settings
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

## Running

```bash
python -m localflow
```

Or install as a systemd user service for auto-start:

```bash
# Create service file
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/localflow.service << 'EOF'
[Unit]
Description=LocalFlow — Speech-to-text with LLM refinement

[Service]
ExecStart=/path/to/python -m localflow
WorkingDirectory=/path/to/LocalFlow
Restart=on-failure

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user enable localflow
systemctl --user start localflow
```

## Architecture

```
localflow/
  __main__.py          # Entry point
  app.py               # QApplication + tray + popup + pipeline wiring
  config.py            # .env config, MCP server registry, mode prompts
  pipeline.py          # QThread worker: record → transcribe → refine → inject

  core/
    recorder.py        # Sounddevice audio recording
    transcriber.py     # Faster Whisper GPU transcription
    refiner.py         # OpenAI/Ollama streaming with tool-calling support
    injector.py        # xdotool text injection

  ui/
    popup.py           # Main popup window
    tray.py            # System tray icon
    waveform.py        # Audio waveform visualization
    styles.py          # Qt stylesheets

  tools/
    base.py            # Tool registry and base classes
    mcp_client.py      # MCP (JSON-RPC over stdio) client
    datetime_tool.py   # Built-in date/time tool

  mcp_servers/
    random_user.py     # Random user data API server
    fitness.py         # Fitness/food tracking API server
    todo.py            # Task management API server
```

## MCP Servers

The `fitness` and `todo` modes use MCP (Model Context Protocol) servers that proxy local APIs. These servers speak JSON-RPC 2.0 over stdio and are spawned automatically when their mode is selected.

- **Fitness server** — Proxies a food tracking API on `localhost:5050` (food entries, daily requirements)
- **Todo server** — Proxies a task management API on `localhost:5050` (CRUD + reorder tasks)

## License

MIT
