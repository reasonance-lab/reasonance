# Reasonance

A collaborative AI reasoning platform that facilitates dialogue between Claude (Anthropic) and GPT (OpenAI). The application enables two LLMs to independently respond to prompts, critique each other's outputs, and iteratively converge on shared conclusions through multiple rounds of discussion.

## Features

- **Dual LLM Conversation**: Claude and GPT respond independently and critique each other
- **Two Conversation Modes**:
  - **Convergence Mode**: Both LLMs provide responses, critique each other, and work toward agreement
  - **Peer Review Mode**: Claude provides a response, GPT reviews it, Claude revises, and GPT re-reviews
- **Automatic Convergence Detection**: Detects when both LLMs agree on conclusions
- **Extended Thinking Support**: Claude's extended thinking with configurable token budget
- **Customizable System Prompts**: Configure prompts for each LLM and mode
- **Real-time Updates**: WebSocket-based UI with live status updates
- **Export Functionality**: Download conversations as markdown

## Prerequisites

- Python 3.12+
- Anthropic API key
- OpenAI API key

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/reasonance-lab/reasonance.git
   cd reasonance
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys** (choose one method):

   **Option A: Environment variables (.env file)**
   ```bash
   # Create a .env file in the project root
   echo "ANTHROPIC_API_KEY=your-anthropic-key" >> .env
   echo "OPENAI_API_KEY=your-openai-key" >> .env
   ```

   **Option B: Enter keys in the UI**
   - Launch the application and click the Settings icon
   - Enter your API keys in the "API Keys" tab

5. **Initialize Reflex**:
   ```bash
   reflex init
   ```

## Usage

### Running the Application

**Development mode**:
```bash
reflex run
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Using the Interface

1. **Enter your prompt** in the text area at the top of the page
2. **Select conversation mode**:
   - Toggle between "Convergence" and "Peer Review" modes using the switch
3. **Start the conversation** by clicking "Start Convergence" or "Start Review"
4. **Monitor progress** as both LLMs respond and critique each other
5. **Review results** in the round-by-round display
6. **Export conversation** using the download button

### Conversation Modes

**Convergence Mode**:
- Both Claude and GPT provide independent initial responses
- Each LLM critiques the other's response
- Process continues until both declare convergence or max rounds reached
- Use "Auto Mode" toggle for automatic progression

**Peer Review Mode**:
- Claude provides an initial response to your prompt
- GPT provides a structured review (strengths, areas for improvement, assessment)
- Claude revises based on feedback
- GPT re-reviews the revision

### Settings

Click the settings icon to configure:

- **API Keys**: Enter or update your Anthropic and OpenAI API keys
- **Model Selection**: Choose Claude and GPT model variants
- **Extended Thinking**: Enable/disable Claude's extended thinking mode
- **System Prompts**: Customize prompts for each LLM and conversation mode
- **Max Rounds**: Set the maximum number of dialogue rounds (default: 10)

## Docker Deployment

**Build and run with Docker**:
```bash
docker build -t reasonance .
docker run -p 80:80 \
  -e ANTHROPIC_API_KEY=your-anthropic-key \
  -e OPENAI_API_KEY=your-openai-key \
  reasonance
```

The application will be available at http://localhost

## Fly.io Deployment

This project is pre-configured for deployment to [Fly.io](https://fly.io). The repository includes a `fly.toml` configuration file ready for deployment.

**Deploy to Fly.io**:

1. **Install the Fly CLI** (if not already installed):
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Authenticate with Fly.io**:
   ```bash
   fly auth login
   ```

3. **Launch the application**:
   ```bash
   fly launch
   ```
   This will detect the existing `fly.toml` and prompt you to configure the deployment.

4. **Set your API keys as secrets**:
   ```bash
   fly secrets set ANTHROPIC_API_KEY=your-anthropic-key
   fly secrets set OPENAI_API_KEY=your-openai-key
   ```

5. **Deploy updates**:
   ```bash
   fly deploy
   ```

The application will be deployed with:
- 1 shared CPU
- 2GB RAM
- Auto-scaling enabled (min: 0 machines)
- HTTPS enforced

## Running Tests

```bash
pytest tests/
pytest tests/ -v  # Verbose output
```

## Project Structure

```
reasonance/
├── llm_convergence/           # Main application
│   ├── llm_convergence.py     # UI entry point
│   ├── state.py               # State management
│   ├── domain/                # Data models and enums
│   ├── services/              # LLM services and orchestration
│   ├── components/            # UI components
│   └── storage/               # Session storage
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
├── rxconfig.py                # Reflex configuration
├── Dockerfile                 # Container definition
└── fly.toml                   # Fly.io deployment config
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Yes |
| `OPENAI_API_KEY` | OpenAI API key for GPT | Yes |
| `REFLEX_ENV` | Set to "prod" for production | No |
| `REFLEX_FRONTEND_PORT` | Frontend port (default: 3000) | No |
| `REFLEX_BACKEND_PORT` | Backend port (default: 8000) | No |

## License

MIT License - see [LICENSE](LICENSE) for details.
