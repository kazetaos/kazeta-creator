## Overview

Kazeta Creator is a command line application that can generate known good self-contained Kazeta cartridges in the `.kzp` format. It can source data from Steam game directories, or from game files downloaded from Itch, Humble, GOG, and elsewhere.

Kazeta Creator cannot generate carts for arbitrary games. Each game must have its details specified in the `contentdb.yaml` file.

The goal of this software is to allow the Kazeta community to share carts without resorting to copyright infringement. The community can safely share recipes for generating the carts instead.

The generated carts are checked against a known good hash, so everyone can play identical, well tested, carts. By extension, this also acts as a compatibility list and a way for the community to share their hard work and make it easier for others to get their favourite games working on Kazeta.

NOTE: The self-contained `.kzp` cart format is not supported in the current stable Kazeta release. You must upgrade to the in-development 2026.0 release.

## Requirements

 - A Linux OS to run Kazeta Creator on
 - An installation of Kazeta (dev build) to run the resulting carts
 - Python 3.x
 - The script uses the following command line tools which may need to be installed:
   - mkfs.erofs
   - xxh3sum
   - curl
   - unzip
   - innoextract
   - magick (ImageMagick)


## Usage

### List available content
To list all available content, run `./kazeta-creator` with no arguments.

The format is the name of the content, followed by its id.

Example output:

```
Balatro | balatro:steam:windows
Celeste | celeste:itch:linux
Mina the Hollower | mina-the-hollower:humble:linux
Mina the Hollower | mina-the-hollower:steam:linux
Sea of Stars | sea-of-stars:gog:windows
A Short Hike | a-short-hike:gog:linux
Xeno Crisis | xeno-crisis:gog:linux
```


### Create a cart
To create a cart, you must first download the required files. Download the files from the indicated provider and for the indicated platform.

For Steam games, you must install the game through Steam.
For other providers, you must download the game files from the provider's website.
Kazeta Creator looks for files in your `Downloads` directory.

Make sure you download or install the correct version of the game, Linux or Windows, as indicated by the id.

Once you have downloaded the required files, run the Kazeta Creator script and pass the cart's id as the first and only argument. You can omit the provider and platform parts of the id if the content is available for only a single provider and platform.

For example, to generate a cart for Balatro, you can run:
 - `./kazeta-creator balatro`

To generate a cart for Mina the Hollower from Humble:
 - `./kazeta-creator mina-the-hollower:humble`

To generate a cart for Mina the Hollower from Steam:
 - `./kazeta-creator mina-the-hollower:steam`


## Future work
 - Documenting the cart definition format
 - Add the ability to directly flash carts to SD cards, flash media, and burn to CD/DVDs
 - Create a static webpage to list details of all available carts on the Kazeta website
 - Design and implement a UI
 - Add support for running Kazeta Creator on Windows for those that do not use Linux
