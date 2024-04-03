import requests
import sys
import urllib.parse

def telegram_message(heading, user, repo, commit, commit_message, job_link):
    message = (
        f"{heading}\n"
        f"User: {user}\n"
        f"Repo: {repo}\n"
        f"Commit: {commit}\n"
        f"Commit Message: {commit_message}\n"
        f"Job Link: {job_link}"
    )
    encoded_message = urllib.parse.quote_plus(message)
    send_text = f'https://api.telegram.org/bot6892843292:AAFRxVctEMkxJMo8YqZu7tFpg2PscTJsQi4/sendMessage?chat_id=-4151868250&parse_mode=Markdown&text={encoded_message}'

    response = requests.get(send_text)
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python telegram.py <heading> <user> <repo> <commit> <commit_message> <job_link>")
        sys.exit(1)

    telegram_message(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
