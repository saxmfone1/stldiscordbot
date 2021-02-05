import os
import discord
from discord.ext import commands
from lib.openscad import generate_png
from lib.thingiverse import ThingiverseClient, ThingInvalidThingException, ThingInvalidIDException, ThingAPIException, ThingInvalidURLException
from tempfile import TemporaryDirectory
import logging
log = logging.getLogger('bot')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


class MissingTokenException(Exception):
    pass


try:
    DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
except KeyError:
    log.error("No discord token provided")
    raise MissingTokenException("No discord token was provided in the env. Please set DISCORD_TOKEN.")

try:
    THINGIVERSE_TOKEN = os.environ["THINGIVERSE_TOKEN"]
except KeyError:
    log.error("No thingiverse token provided")
    raise MissingTokenException("No thingiverse token was provided in the env. Please set THINGIVERSE_TOKEN.")

thing_client = ThingiverseClient(THINGIVERSE_TOKEN)
log.debug("Setting up thingiverse api")


def get_pngs_from_thingiverse(tempdir, thing):
    log.debug(f"Trying to pull down thingid: {thing} and store it in {tempdir}")
    pngs = []
    stls = thing_client.get_stls(thing)
    files = thing_client.download_stls(tempdir, stls)
    for file in files:
        log.debug(f"found stl: {file}")
        png = generate_png(tempdir, file)
        pngs.append(png)
    return pngs


def get_pngs_from_attachment(tempdir, stls):
    log.debug(f"Trying to pull down attachment: {stls} and store it in {tempdir}")
    pngs = []
    for file in stls:
        log.debug(f"found stl: {file}")
        png = generate_png(tempdir, file)
        pngs.append(png)
    return pngs


bot = commands.Bot(command_prefix='!')


@bot.command(name='thing')
async def show_thing(ctx, thing=""):
    if thing == "":
        log.debug("!thing called with no arguments")
        await ctx.send("you forgot to post a thing!")
    else:
        log.info(f"!thing called for {thing}")
        with TemporaryDirectory() as tempdir:
            log.debug(f"created tempdir: {tempdir}")
            try:
                pngs = get_pngs_from_thingiverse(tempdir, thing)
            except ThingInvalidThingException:
                ctx.send("this is not a valid thing!")
            if len(pngs) > 0:
                for png in pngs:
                    log.debug(f"sending {png} to discord")
                    await ctx.send(file=discord.File(png))
                    log.debug(f"{png} sent")
            else:
                ctx.send("there were no stls found on this thing")


@bot.command(name='stl')
async def convert_stl(ctx: commands.Context):
    if len(ctx.message.attachments) > 0:
        log.info(f"!stl called with attachments")
        with TemporaryDirectory() as tempdir:
            log.debug(f"created tempdir: {tempdir}")
            stls = []
            for attachment in ctx.message.attachments:
                if attachment.filename.endswith(".stl"):
                    log.info(f"found stl in attachment {attachment.filename}")
                    thing = f"{os.path.basename(attachment.filename)}"
                    log.debug(f"saving attachment to {tempdir}/{thing}")
                    await attachment.save(f"{tempdir}/{thing}")
                    stls.append(f"{tempdir}/{thing}")

            if len(stls) > 0:
                pngs = get_pngs_from_attachment(tempdir, stls)
                for png in pngs:
                    log.debug(f"sending {png} to discord")
                    await ctx.send(file=discord.File(png))
                    log.debug(f"{png} sent")
            else:
                log.info("No stls were attached")
                await ctx.send("None of the attachments were stls")
    else:
        log.info("!stl called with no attachments")
        await ctx.send("You forgot to attach an stl!")


@bot.event
async def on_connect():
    log.info("Connected to discord!")

bot.run(DISCORD_TOKEN)
