import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.summarize import summarize_transcript


def _load_dotenv_if_present() -> None:
    env_path = Path(__file__).resolve().parents[1] / '.env'
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = (raw_line or '').strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    _load_dotenv_if_present()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('Missing OPENAI_API_KEY (set backend/.env or env var)')

    fake_transcript = """
Speaker 1: Hi, thanks for joining. I wanted to quickly sync on the upcoming AI feature for EchoBrief. We need to finalize the roadmap.
Speaker 2: Sure. I’ve looked at the Whisper API integration. It’s looking good, but we need to decide on the file size limit for the MVP.
Speaker 1: Good point. Let’s cap it at 25MB for now to keep the processing time under a minute. We can scale it later.
Speaker 2: Agreed. 25MB is reasonable. I’ll implement the validation on the backend by Wednesday.
Speaker 1: Perfect. Also, the marketing team needs a demo video. Can you prepare a recording of the current flow?
Speaker 2: I can do that, but I’ll need the new UI components from Rotem first.
Speaker 1: I’ll talk to Rotem today and make sure you get those Figma assets by tomorrow morning. Once you have them, please send me the demo by Thursday EOD.
Speaker 2: Sounds like a plan. So, 25MB limit and demo by Thursday. Anything else?
Speaker 1: That’s it for now. Let’s move forward with these.
""".strip()

    result = summarize_transcript(transcript=fake_transcript, openai_api_key=api_key)
    print(
        json.dumps(
            {
                'summary': result.summary,
                'participants': result.participants,
                'decisions': result.decisions,
                'action_items': [i.model_dump() for i in result.action_items],
                'model': result.model,
                'cached': result.cached,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == '__main__':
    main()

