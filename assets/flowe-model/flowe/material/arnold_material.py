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


# NOTE : supports Arnold v 3.0.0+


from .materials import (
    filter_tex_maps,
)

import maya.cmds as cmds


TEX_MAP_ATTRS = {
    "AmbientOcclusion": {
        "colorspace": "sRGB",
        "connect": ("outColor", "input2"),
    },
    "BaseColor": {
        "colorspace": "sRGB",
        "connect": ("outColor", "baseColor"),
    },
    "BaseColorOpacity": {
        "colorspace": "sRGB",
        "connect": ("outColor", "baseColor"),
    },
    "Displacement": {
        "colorspace": "Raw",
        "connect": ("outColor", "displacement"),
    },
    "Emission": {
        "colorspace": "sRGB",
        "connect": ("outColor", "emissionColor"),
    },
    "MaskMap": {
        "colorspace": "sRGB",
        "connect": ("outColor", ""),
    },
    "Metallic": {
        "colorspace": "Raw",
        "connect": ("outColorR", "metalness"),
    },
    "Normal": {
        "colorspace": "Raw",
        "connect": ("outColor", "input"),
    },
    "Opacity": {
        "colorspace": "Raw",
        "connect": ("outColor", "opacity"),
    },
    "Roughness": {
        "colorspace": "Raw",
        "connect": ("outColorR", "specularRoughness"),
    },
    "ScatteringColor": {
        "colorspace": "sRGB",
        "connect": ("outColor", "subsurfaceRadius"),
    },
    "SheenColor": {
        "colorspace": "sRGB",
        "connect": ("outColor", "sheenColor"),
    },
    "Translucency": {
        "colorspace": "sRGB",
        "connect": ("outColor", "subsurfaceColor"),
    },
    "Transmission": {
        "colorspace": "Raw",
        "connect": ("outColorR", "transmission"),
    },
}


class ArnoldMaterial():
    
    # engine_name: str = "Arnold"
    # mat_name: str = None
    # workflow: str = "METALNESS"
    # shading_engine: str = None
    # material: str = None
    # nodes: dict = {}
    
    def __init__(
            self,
            mat_name=""):
        
        self.mat_name = mat_name
        self.engine_name = "Arnold"
        self.workflow = "METALNESS"
        self.shading_engine = None
        self.material = None
        self.nodes = {}
    
    # ------------------------------------------------------------------------------------
    
    def build_material(
            self,
            workflow="",
            tex_maps={}):
        """Function that creates material for Arnold material class.
        
        The input structure allows articulating the creation of a given size
        (texture resolution) and workflow (Regular or Metalness) material.
        """
        
        tex_maps = filter_tex_maps(tex_maps)
        
        try:
            self.material = self._build_metalness(tex_maps)
            return self.material
            
        except Exception as err:
            print(err)
            raise Exception("Material failed to build.")
        
        return None
    
    # ------------------------------------------------------------------------------------
    
    def _build_metalness(
            self,
            tex_maps={}):
        """ Builds a Metalness material """
        
        self.shading_engine = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="{}_SG".format(self.mat_name))
        
        self.material = cmds.shadingNode("aiStandardSurface", asShader=True, name=self.mat_name)
        
        cmds.connectAttr("{}.outColor".format(self.material), "{}.surfaceShader".format(self.shading_engine), force=True)
        
        self.nodes = {}
        
        for tex_map, file in tex_maps.items():
            self.nodes[tex_map] = image_node = self._create_image_node(tex_map, file)
            
            self._connect_image_node(tex_map, image_node, self.material)
        
        self._connect_basecoloropacity()
        
        self._create_basecolor_mix()
        
        self._create_displacement_setup()
        
        self._create_emission_setup()
        
        self._create_normal_setup()
        
        self._create_sheen_setup()
        
        self._create_subsurface_setup()
        
        self._create_translucency_setup()
        
        self._create_transmission_setup()
        
        return self.material
    
    # ------------------------------------------------------------------------------------
    
    def _connect_basecoloropacity(self):
        """ Connect BaseColorOpacity """
        
        col_node = self.nodes.get("BaseColorOpacity", None)
        if col_node is None:
            return
        
        # ......................................................................
        
        for ch in ["R", "G", "B"]:
            cmds.connectAttr("{}.outAlpha".format(col_node), "{}.opacity.opacity{}".format(self.material, ch), force=True)
    
    def _create_basecolor_mix(self):
        """ Creates an aiLayerRgba node to mix AO and BaseColor """
        
        col_node = self._get_color_node()
        if col_node is None:
            return
        
        ao_node = self.nodes.get("AmbientOcclusion", None)
        if ao_node is None:
            return
        
        # ......................................................................
        
        self.nodes["AO_Mix"] = mix_node = cmds.shadingNode("aiLayerRgba", asTexture=True, name="{}_AO_Mix".format(self.mat_name))
        cmds.setAttr("{}.enable2".format(mix_node), 1)
        cmds.setAttr("{}.operation2".format(mix_node), 23)
        cmds.setAttr("{}.mix2".format(mix_node), 0)
        cmds.connectAttr("{}.outColor".format(mix_node), "{}.baseColor".format(self.material), force=True)
        
        cmds.connectAttr("{}.outColor".format(col_node), "{}.input1".format(mix_node), force=True)
        
        cmds.connectAttr("{}.outColor".format(ao_node), "{}.input2".format(mix_node), force=True)
    
    def _create_displacement_setup(self):
        """ Builds a Displacement map setup """
        
        displacement_node = self.nodes.get("Displacement", None)
        if displacement_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Displacement_Node"] = disp_node = cmds.shadingNode("displacementShader", asShader=True, name="{}_Displacement_Node".format(self.mat_name))
        cmds.setAttr("{}.scale".format(disp_node), 0)
        cmds.connectAttr("{}.displacement".format(disp_node), "{}.displacementShader".format(self.shading_engine), force=True)
        
        cmds.connectAttr("{}.outColorR".format(displacement_node), "{}.displacement".format(disp_node), force=True)
    
    def _create_emission_setup(self):
        """ Builds an Emission map setup """
        
        emission_node = self.nodes.get("Emission", None)
        if emission_node is None:
            return
        
        # ......................................................................
        
        cmds.setAttr("{}.emission".format(self.material), 0)
    
    def _create_normal_setup(self):
        """ Builds a Normal map setup """
        
        normal_node = self.nodes.get("Normal", None)
        if normal_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Normal_Node"] = nrm_node = cmds.shadingNode("aiNormalMap", asTexture=True, name="{}_Normal_Node".format(self.mat_name))
        cmds.setAttr("{}.tangentSpace".format(nrm_node), 1)
        cmds.connectAttr("{}.outValue".format(nrm_node), "{}.normalCamera".format(self.material), force=True)
        
        cmds.connectAttr("{}.outColor".format(normal_node), "{}.input".format(nrm_node), force=True)
    
    def _create_sheen_setup(self):
        """ Builds a Sheen setup """
        
        sheen_node = self.nodes.get("SheenColor", None)
        if sheen_node is None:
            return
        
        # ......................................................................
        
        cmds.setAttr("{}.sheen".format(self.material), 1)
        cmds.setAttr("{}.sheenRoughness".format(self.material), 0.1)
    
    def _create_subsurface_setup(self):
        """ Builds a Subsurface setup """
        
        sss_node = self.nodes.get("ScatteringColor", None)
        if sss_node is None:
            return
        
        # ......................................................................
        
        col_node = self._get_color_node()
        
        if col_node is not None:
            cmds.connectAttr("{}.outColor".format(col_node), "{}.subsurfaceColor".format(self.material), force=True)
        
        # ......................................................................
        
        cmds.setAttr("{}.subsurface".format(self.material), 1)
        cmds.setAttr("{}.subsurfaceScale".format(self.material), 1)
        cmds.setAttr("{}.subsurfaceType".format(self.material), 2)
    
    def _create_translucency_setup(self):
        """ Builds a Translucency setup """
        
        translucency_node = self.nodes.get("Translucency", None)
        if translucency_node is None:
            return
        
        # ......................................................................
        
        cmds.setAttr("{}.subsurface".format(self.material), 0.35)
        cmds.setAttr("{}.thinWalled".format(self.material), 1)
    
    def _create_transmission_setup(self):
        """ Builds a Transmission setup """
        
        transmission_node = self.nodes.get("Transmission", None)
        if transmission_node is None:
            return
        
        # ......................................................................
        
        col_node = self._get_color_node()
        
        if col_node is not None:
            cmds.connectAttr("{}.outColor".format(col_node), "{}.transmissionColor".format(self.material), force=True)
        
        # ......................................................................
        
        cmds.setAttr("{}.transmissionDepth".format(self.material), 10)
    
    # ------------------------------------------------------------------------------------
    
    def _get_color_node(self):
        """ Gets Color node """
        
        col_node = self.nodes.get("BaseColor", None)
        if col_node is None:
            col_node = self.nodes.get("BaseColorOpacity", None)
        
        return col_node
    
    def _create_image_node(
            self,
            tex_map="",
            file=""):
        """ Creates an Image node,
        sets the filename path,
        sets the colorSpace
        """
        
        image_node = cmds.shadingNode("aiImage", asTexture=True, name="{}_{}".format(self.mat_name, tex_map))
        
        cmds.setAttr("{}.filename".format(image_node), file, type="string")
        
        colorspace = TEX_MAP_ATTRS.get(tex_map, {}).get("colorspace", "Raw")
        cmds.setAttr("{}.colorSpace".format(image_node), colorspace, type="string")
        
        return image_node
    
    def _connect_image_node(
            self,
            tex_map="",
            image_node="",
            target_node=""):
        """ Connects image_node to target_node with relevant attrs """
        
        out_attr, target_attr = TEX_MAP_ATTRS.get(tex_map, {}).get("connect", ("", ""))
        
        if out_attr not in cmds.listAttr(image_node) or target_attr not in cmds.listAttr(target_node):
            return
        
        cmds.connectAttr("{}.{}".format(image_node, out_attr), "{}.{}".format(target_node, target_attr), force=True)
