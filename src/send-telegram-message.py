import requests
import sys

magnitude = sys.argv[1]

TOKEN = "[REDACTED]"
chat_id = "[REDACTED]"
message = f"TCrB_ALERT: Magnitude {magnitude}"
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
print(requests.get(url).json()) # this sends the message
