# stldiscordbot
Discord bot to help with 3d printering

# Prerequisites
* Discord Developer Account
* Thingiverse Developer Account

### Either
* Openscad
* Python 3
### Or
* Docker

# How to start
## Docker (Recommended)
Build image:

`docker build -t stldiscordbot .`

Run image:

`docker run -d -e THINGIVERSE_TOKEN=<token> -e DISCORD_TOKEN=<token> stldiscordbot`

## Python
Install openscad and python3
Set the location of the openscad binary in `lib/openscad.py`
Install python dependencies:

`pip install -r requirements.txt`

Run bot:

`python3 ./bot.py`

# Using the bot
The bot responds to commands in discord channels

## !thing \<thing\>
Downloads stl files from thingiverse for a given thing, generates an image and posts back to the channel. <thing> can either be a url or thing id.

## !stl (with attachment)
Generates an image for the attached stl and posts back to the channel