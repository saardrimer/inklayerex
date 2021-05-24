# MIT License
#
# Copyright (c) 2021 Saar Drimer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import subprocess
import argparse
import re
import copy
from pathlib import Path
from lxml import etree as et
from typing import Dict, Any

NS_SVG = "http://www.w3.org/2000/svg"
NS_INK = "http://www.inkscape.org/namespaces/inkscape"


def parse_cli_args() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config-file", action="store", type=str, required=True)
    ap.add_argument("-s", "--svg-file", action="store", type=str, required=True)
    args = ap.parse_args()
    return args


def open_svg(f: str) -> et:
    data = et.ElementTree(file=f)
    return data


def get_all_layers(d: et) -> list:
    """Find all the Inkscape layers in the SVG"""
    nss = {"svg": NS_SVG, "inkscape": NS_INK}
    layers_l = d.findall('//svg:g[@inkscape:groupmode="layer"]', namespaces=nss)
    return layers_l


def read_json_file(f: Path) -> Dict:
    with open(f) as jf:
        d = json.load(jf)
    return d


def replace_or_add_style_prop(style_str, prop_name, new_prop_value):
    """
    Find `prop_name` in `style_str` and replace it with `new_prop_value`. If
    `prop_name` isn't in `style_str`, then add it with `new_prop_value` to the end
    of the string.
    """
    search_str = f"\s*?{prop_name}\s*?:\s*?([-\w]*)"
    re_result = re.findall(search_str, style_str)
    if re_result == []:
        style_str += f";{prop_name}:{new_prop_value}"
    else:
        search_str = f"\s*?{prop_name}\s*?:\s*?{re_result[0]}"
        style_str = re.sub(search_str, f"{prop_name}:{new_prop_value}", style_str)
    return style_str


def get_prop_value(style_str, prop_name):
    """Get the property value from a style string"""
    search_str = f"\s*?{prop_name}\s*?:\s*?([-\w]*)"
    re_result = re.findall(search_str, style_str)
    return re_result[0]


def reset_visibility(layers_l: list) -> None:
    """Hide all layers in the input list"""
    for layer in layers_l:
        style_str = layer.get("style")
        style_str = replace_or_add_style_prop(style_str, "display", "none")
        layer.set(f"style", style_str)


def set_visibility(layers_l: list, set_l: list) -> list:
    """Make layers in 'layers_l' with name that's in 'set_l' visible"""
    for layer in layers_l:
        if layer.get(f"{{{NS_INK}}}label") in set_l:
            style_str = layer.get("style")
            style_str = replace_or_add_style_prop(style_str, "display", "inline")
            layer.set(f"style", style_str)


def save_svg_file(svg_data: et, f: Path) -> None:
    f.write_text(et.tostring(svg_data, encoding="unicode", pretty_print=True))


def del_invisible_layers(svg_data):
    """Remove all layers that are set to not be displayed"""
    layers_l = get_all_layers(svg_data)
    for layer in layers_l:
        style_str = layer.get("style")
        prop = get_prop_value(style_str, "display")
        if prop == "none":
            layer.getparent().remove(layer)
    return svg_data


def main():

    args = parse_cli_args()

    # Read in the configuration file
    json_file = Path(args.config_file)
    cfg_d = read_json_file(json_file)

    # Open the SVG and extract references to all layers
    fn = args.svg_file  # cfg_d['svg-input-file']
    svg_data = open_svg(fn)
    layers_l = get_all_layers(svg_data)

    # Get build sub-path from config file (or default) and create it if not there
    build_path = Path(cfg_d.get("build-path", "generated"))
    build_path.mkdir(parents=True, exist_ok=True)

    inkscape_args = cfg_d.get("inkscape-args", "")  # Inkscape arguments
    del_layers = cfg_d.get(
        "del-invisible-layers-on-save", False
    )  # delete the invisible layers?
    del_svgs = cfg_d.get("del-generated-svgs", False)  # delete generated SVGs?
    im_convert = cfg_d.get("im-convert", False)  # convert further with `convert`?
    im_convert_format = cfg_d.get("im-convert-format", "jpg").lstrip(".")  # img format?
    im_convert_args = cfg_d.get("im-convert-args", [])  # `convert` arguments

    # Get the 'generate' list and add the 'always include' list to each list.
    gen_d = cfg_d.get("generate", {})
    always_include_l = cfg_d.get("always-include", [])
    for name, l in gen_d.items():
        l += always_include_l

    # Add the 'standalone' dict to the 'generate' list. Keys must be unique.
    gen_sa_d = cfg_d.get("generate-standalone", {})
    gen_d.update(gen_sa_d)

    # Create SVG with appropriate layer visibility;
    # convert to image using Inkscape;
    # delete SVG if defined;
    # run `convert` for further conversion if defined
    for name, set_l in gen_d.items():
        svg_file_out = build_path / f"{name}.svg"
        reset_visibility(layers_l)
        set_visibility(layers_l, set_l)
        if del_layers is True:
            svg_data_save = del_invisible_layers(copy.deepcopy(svg_data))
        else:
            svg_data_save = svg_data
        save_svg_file(svg_data_save, svg_file_out)
        command = ["inkscape"] + inkscape_args + [str(svg_file_out)]
        subprocess.run(command)  # run 'inkscape' command
        if del_svgs is True:
            svg_file_out.unlink(missing_ok=True)  # delete file
        if im_convert is True:
            infile = build_path / f"{name}.png"
            outfile = build_path / f"{name}.{im_convert_format}"
            command = (
                ["convert", f"{str(infile)}"] + im_convert_args + [f"{str(outfile)}"]
            )
            subprocess.run(command)  # run 'convert' command


if __name__ == "__main__":
    main()
