import subprocess
import openai
from openai import OpenAI
import click
import os
import tempfile

@click.command()
def main():
    """
    This script generates a git commit message using OpenAI GPT based on the output of `git diff --cached`.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable not set.", err=True)
        exit(1)

    openai.api_key = api_key
    changes = get_git_changes()

    if not changes:
        click.echo("No changes to commit.")
        return

    commit_message = generate_commit_message(changes)
    edit_commit_message(commit_message)

def get_git_changes():
    result = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True)
    return result.stdout

def generate_commit_message(changes):
    try:
        client = OpenAI()
        print("Generating commit message...")
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                    "role": "user",
                    "content": """You are writing one git commit message based on git diffs.
                    
                    The format of the message should be:
                    <<summary line (60 chars max)>>
                    <<blank line>>
                    <<paragraph describing the changes>>
                    
                    Notes:
                    add newlines in the paragraph to keep the max line length at 80 characters
                    describe changes imperitively
                    do not mention changes to imports
                    do not mention that the message was geneated by AI"""
                },
                {
                    "role": "user",
                    "content": "here is the diff: " + changes
                }
            ],
            stream=True
        )
        
        commit_message = ""
        for part in stream:
            commit_message += part.choices[0].delta.content or ""

        return commit_message
    except Exception as e:
        click.echo("Error in generating commit message: " + str(e), err=True)
        exit(1)

def edit_commit_message(commit_message):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
        tmp_file.write(commit_message)
        tmp_file_path = tmp_file.name

    editor = subprocess.check_output(['git', 'var', 'GIT_EDITOR']).strip().decode('utf-8')
    subprocess.call([editor, tmp_file_path])

    with open(tmp_file_path, 'r') as file:
        final_commit_message = ""
        for line in file:
            if not line.strip().startswith('#'):
                final_commit_message += line


    if not final_commit_message.strip():
        click.echo("Commit aborted: no commit message provided after editing.")
        return

    subprocess.call(['git', 'commit', '-F', tmp_file_path])
    os.unlink(tmp_file_path)


if __name__ == "__main__":
    main()
