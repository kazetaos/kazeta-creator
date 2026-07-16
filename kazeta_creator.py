import os
import re
import glob
import uuid
import yaml
import subprocess
from pathlib import Path

FILE_DIR = os.path.join(Path.home(), 'Downloads')
STEAM_DIR = os.path.join(Path.home(), '.steam/steam/steamapps/common')
HEROIC_DIR=os.path.join(Path.home(), 'Games/Heroic')

def xxh3sum(path):
    result = subprocess.run(["xxh3sum", path], capture_output=True, text=True)
    return result.stdout[5:21]

def xxh3_check(path, expected, log_cb):
    actual = xxh3sum(path)
    if actual != expected:
        log_cb(f"ERROR: xxh3sum mismatch: {os.path.basename(path)}")
        log_cb(f"Expect: {expected}")
        log_cb(f"Actual: {actual}")
        return False
    return True

def load_database(yaml_path='contentdb.yaml'):
    # loads the YAML database and returns the list of games
    with open(yaml_path) as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.FullLoader)

def build_game(game, log_cb=print, compression="lz4"):
    dst_dir = game['id']
    download_dir = dst_dir + '_download'
    staging_dir = dst_dir + '_staging'

    log_cb("Cleaning previous directories...")
    subprocess.run(["rm", "-rf", dst_dir])
    subprocess.run(["mkdir", dst_dir])

    if 'sources' not in game:
        raise Exception('No sources found in game config.')

    for source in game['sources']:
        if 'uri' not in source:
            raise Exception('Missing `uri` key in source.')

        uri = source['uri']
        subprocess.run(["rm", "-rf", download_dir])
        subprocess.run(["rm", "-rf", staging_dir])
        subprocess.run(["mkdir", download_dir])
        subprocess.run(["mkdir", staging_dir])

        # find/fetch files
        basename = os.path.basename(uri)
        log_cb(f"Fetching source: {basename}...")

        if uri.startswith('file://'):
            path = os.path.join(FILE_DIR, basename)
        elif uri.startswith('steam://'):
            path = os.path.join(STEAM_DIR, basename)
        elif uri.startswith('epic://'):
            path = os.path.join(HEROIC_DIR, basename)
        elif uri.startswith('amazon://'):
            path = os.path.join(HEROIC_DIR, basename)
        elif uri.startswith('https://'):
            subprocess.run(["curl", "--progress-bar", "-LO", "--output-dir", download_dir, uri])
            path = os.path.join(download_dir, basename)
            if path.endswith('.AppImage'):
                subprocess.run(["chmod", "+x", path])
        else:
            raise Exception(f'Unknown URI format: {uri}')

        if not os.path.exists(path):
            raise Exception(f"File or directory not found: {path}")

        # check hash
        if 'xxh3sum' in source and os.path.isfile(path):
            log_cb("Verifying hash...")
            if not xxh3_check(path, source['xxh3sum'], log_cb):
                raise Exception("Hash verification failed.")

        if 'process' in source and source['process'] == False:
            continue

        # extract files
        log_cb("Extracting files...")
        if path.endswith('.tar') or '.tar.' in path:
            subprocess.run(["tar", "-xf", path, "-C", staging_dir])
        elif path.endswith('.zip') or path.endswith('.sh') or path.endswith('-bin'):
            subprocess.run(["unzip", "-q", path, "-d", staging_dir])
        elif path.endswith('.exe'):
            subprocess.run(["innoextract", "--silent", "--progress=1", path, "-d", staging_dir])
        elif path.endswith('.ico') and 'include' in source and 'destination' in source:
            subprocess.run(["magick", path + '[' + str(source['include']) + ']', "-strip", os.path.join(dst_dir, source['destination'])])
            continue
        elif os.path.isdir(path):
            src_files = glob.glob(path + '/*')
            for f in src_files:
                subprocess.run(["cp", "-r", f, staging_dir + '/'])
        else:
            subprocess.run(["cp", path, staging_dir + '/'])

        # exclude filter
        if 'exclude' in source:
            excludes = source['exclude']
            if not isinstance(excludes, list):
                excludes = [ excludes ]
            for e in excludes:
                files = glob.glob(os.path.join(staging_dir, e))
                for f in files:
                    subprocess.run(["rm", "-rf", f])

        final_dst = dst_dir
        if 'destination' in source:
            final_dst = os.path.join(dst_dir, source['destination'])

        # include filter
        includes = source.get('include', '*')
        if not isinstance(includes, list):
            includes = [ includes ]

        log_cb("Moving files to destination...")
        for e in includes:
            src_files = glob.glob(os.path.join(staging_dir, e))
            for f in src_files:
                subprocess.run(["mv", f, final_dst])

    # clean up
    log_cb("Cleaning up temporary directories...")
    subprocess.run(["rm", "-rf", download_dir])
    subprocess.run(["rm", "-rf", staging_dir])

    icon_path = os.path.join(game['id'], 'org.kazeta.icon.png')
    if not os.path.exists(icon_path):
        log_cb("WARNING: no icon found (org.kazeta.icon.png)")

    log_cb("Generating configuration files...")
    with open(os.path.join(game['id'], 'org.kazeta.cart.kzi'), 'w', encoding='utf-8') as file:
        file.write(f"Name={game['name']}\n")
        file.write(f"Id={game['id']}\n")
        file.write(f"Exec={game['exec']}\n")
        file.write("Icon=org.kazeta.icon.png\n")
        if 'runtime' in game and game['runtime'] != 'none':
            file.write(f"Runtime={game['runtime']}\n")

    if 'steam_app_id' in game:
        with open(os.path.join(game['id'], 'steam_appid.txt'), 'w', encoding='utf-8') as file:
            file.write(str(game['steam_app_id']))

    kzp = game['id'] + '.kzp'
    subprocess.run(["rm", "-rf", kzp])

    uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'org.kazeta.' + game['id']))
    log_cb(f"Creating EROFS filesystem image ({compression} compression)...")
    subprocess.run(["mkfs.erofs", "-T", "0", "-U", uid, f"-z{compression}", kzp, game['id']])
    subprocess.run(["rm", "-rf", game['id']])

    if 'xxh3sum' in game:
        log_cb("Verifying final image hash...")
        xxh3_check(kzp, game['xxh3sum'], log_cb)

    log_cb(f"Build complete: {kzp}")
