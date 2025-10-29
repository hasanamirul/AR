##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


NORMAL_MAPS = [
    "Normal"
]

DISPLACEMENT_MAPS = [
    "Displacement"
]

EMISSION_MAPS = [
    "Emission"
]


# ==================================================================================================

TEX_FILTERS = {
    "BaseColorOpacity": [
        "BaseColor",
        "Opacity",
    ],
    "MaskMap": [
        "AmbientOcclusion",
        "Metallic",
        "Roughness",
    ],
    "ScatteringColor": [
        "Translucency",
        "Transmission",
    ],
}


def filter_tex_maps(tex_maps={}):
    """ Filters out unnecessary tex maps
    
    eg. BaseColorOpacity replaces BaseColor and Opacity
    """
    
    # print(json.dumps(tex_maps, indent=2))
    
    for tex_map in TEX_FILTERS:
        if tex_map not in tex_maps:
            continue
        
        for remove_map in TEX_FILTERS[tex_map]:
            tex_maps.pop(remove_map, None)
    
    # print(json.dumps(tex_maps, indent=2))
    
    return tex_maps
