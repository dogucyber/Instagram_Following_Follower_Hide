# Instagram Following Follower Hide

<img width="2172" height="724" alt="Instagram" src="https://github.com/user-attachments/assets/8286c2dc-2602-451e-91b3-568c6399e363" />

## Description
A command-line tool for managing the setting that hides your Instagram follower and following lists. It provides two Python scripts, one to enable the setting and one to disable it.

## Scripts

| File | Purpose |
| --- | --- |
| `hide.py` | Requests that Instagram enable hiding for the follower and following lists. |
| `show.py` | Requests that Instagram disable the same setting. |

## Requirements

Both scripts use the Python standard library and were tested with Python 3.12. You can run either script directly from a terminal.

## Usage

Open a terminal in the folder containing the scripts and run the command for the action you want to perform.

### Enable list hiding

```bash
python hide.py
```

### Disable list hiding

```bash
python show.py
```

When prompted, enter the value of the Instagram `sessionid` cookie for the account you want to update and press Enter. Enter only the value that follows `sessionid=`.

## How it works

The script reads the account ID from the session value and sends a single GraphQL request to Instagram. Both scripts target the `hide_followers_following_list` setting. The hide script sends `true` and the show script sends `false`.

The script checks the setting value in Instagram's response. It displays a confirmation if Instagram returns the requested value. Connection failures, server errors, and unexpected responses produce an error message.

## Verify the result

The confirmation means Instagram returned the requested setting value. To check how the profile appears to others, open it from another Instagram account and view the follower and following lists separately.

<img width="562" height="680" alt="image" src="https://github.com/user-attachments/assets/e93b5fb3-3f3b-43f0-886d-68d4a952557a" />
