import os
import os.path
import sarge
import logging

log = logging.getLogger("bot.openscad")


OPENSCAD = "/usr/bin/openscad"
log.debug(f"using openscad binary: {OPENSCAD}")


def get_base_filename(filename: str):
    return "".join(os.path.basename(filename).split(".")[:1])


def generate_scad(tempdir: str, filename: str):
    log.debug(f"generating scad from stl: {filename} and storing it in {tempdir}")
    content = f'import("{filename}");'
    base_scad = get_base_filename(filename)
    scad_filename = f"{tempdir}/{base_scad}.scad"
    log.debug(f"saving {scad_filename}")
    with open(scad_filename, "w") as f:
        f.write(content)
    log.debug(f"saved {scad_filename}")
    return scad_filename


def generate_png(tempdir: str, filename: str):
    log.info(f"generating png from stl: {filename} and storing it in {tempdir}")
    scad_file = generate_scad(tempdir, filename)
    base_png = get_base_filename(filename)
    png_filename = f"{tempdir}/{base_png}.png"
    log.debug(f"saving {png_filename}")
    cmd = [OPENSCAD, '-o', png_filename, '--autocenter', '--viewall', '--quiet', scad_file]
    out = sarge.capture_both(cmd)
    log.debug(f"openscad output: {out.stdout.text}")
    log.error(f"openscad output: {out.stderr.text}")
    return png_filename
