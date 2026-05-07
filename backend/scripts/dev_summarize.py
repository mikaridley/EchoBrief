import os
import json

from app.services.summarize import summarize_transcript


def main() -> None:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('Missing OPENAI_API_KEY env var (load backend/.env first)')

    fake_transcript = """
Speaker 1: Okay quick sync. We need a landing page by next Tuesday.
Speaker 2: I can draft the copy today. Design can be minimal.
Speaker 1: Decision: ship with the existing template and just update the hero section.
Speaker 2: Action item: I will send copy by EOD. You’ll update the page tomorrow.
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

