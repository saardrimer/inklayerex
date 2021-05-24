## inklayerex

This Python script converts certain specified layers in an Inkscape SVG into a series of images based on a definition in a JSON file.

### Requirements

* Python 3.8+  
* Inkscape 1.0+  
* lxml  
* `convert` from imagemagick (optional)

### Operation

You'll need two files:

_An Inkscape SVG:_ Prepare an SVG with layers that you'd like to turn on or off when creating images. Inkscape allows sub-layers and those are fine as long as _all layer names are unique_.

_A JSON config file:_ This file defines some parameters, the switches that go to the programs that are called (`Inkscape`, and optionally `convert`), and which layers to show or hide for each generated image.

The script simply loads the SVG, hides all layers, and then 'enables' the layers that according to the image definition in the JSON file. Then, it calls Inkscape to convert the SVG to PNG, and (optionally) then calls `convert` to convert the images further (`convert` has many more options for image manipulation than Inkscape's converter, of course). 

The following is `example.json` that's included in this repository.

```
{
    "del-invisible-layers-on-save": false, # delete invisible layers before saving SVG?
    "del-generated-svgs": true, # delete the intermediate SVGs?
    "build-path": "generated", # path for where to place generated files
    "inkscape-args": [ # arguments switches for Inkscape (see 'inkscape --help')
        "--export-overwrite",
        "--export-area-page",
        "--export-type=png",
        "--export-dpi=200",
        "--export-background=#ffffff",
        "--export-background-opacity=255"
    ],
    "im-convert": true, # convert image further with 'convert'?
    "im-convert-format": "jpg", # the extention format for 'convert'
    "im-convert-args": [ # 'convert' switches (see 'convert --help')
        "-resize", "2000",
        "-strip",
        "-flatten",
        "-quality", "85%",
        "-define", "webp:lossless=true" # useful if you use 'webp' as output format
    ],
    "always-include": [ # layer names to always include in the image
        "ground",
        "sky"
    ],
    "generate": { # the list of images to generate including 'always-include' layers
        "path": [ # the name of the generated image
            "path" # include this layer (+'ground'+'sky')
        ],
        "path-sun": [
            "path",
            "sun"
        ],
        "path-sun-mirage": [ # the name of the image
            "path", # include this layer
            "sun", # and also this layer
            "mirage" # and... this one too
        ],
        "sun-mirage": [
            "sun",
            "mirage"
        ]
   },
    "generate-standalone": {  # list of images to generate without 'always-include'
        "welcome-screen": [
            "welcome",
            "sun"
        ],
        "the-end-screen": [
            "the-end",
            "path"
        ]
    }
}
```

Please note:
* All image name keys -- in `generate` and `generate-standalone` combined! -- must be unique, otherwise the images will be overwritten. 
* Arguments to callable programs shouldn't have a space; so `-quality 85%`, for example, should be specified as `"-quality", "85%"`
* If the defined layer name isn't in the SVG, it'll be ignored.
* That JSON above is invalid because it has comments :)

### Running

Once you have an SVG and a config file, run

    python3 inklayerex.py -c <config_file.json> -s <svg_file.svg>

or on the example files in `/example`

    python3 inklayerex.py -c example/example.json -s example/example.svg

and look at the generated files in `/generated`.

### Notes

I've only tested this software on Linux. There might be a way to make it run on other OSs, but I'm not sure you'll get the same results.

### License

MIT; see the `LICENSE` file.
