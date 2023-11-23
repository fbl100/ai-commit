import subprocess
import openai
import click
import os

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
    click.echo(commit_message)

def get_git_changes():
    result = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True)
    return result.stdout

def generate_commit_message(changes):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="Generate a git commit message for these changes:\n\n" + changes,
            max_tokens=60
        )
        return response.choices[0].text.strip()
    except Exception as e:
        click.echo("Error in generating commit message: " + str(e), err=True)
        exit(1)

if __name__ == "__main__":
    main()
