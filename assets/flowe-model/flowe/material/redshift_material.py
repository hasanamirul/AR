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


# NOTE : supports Redshift v 2.6.0+


from .materials import (
    filter_tex_maps,
)

import maya.cmds as cmds


TEX_MAP_ATTRS = {
    "AmbientOcclusion": {
        "colorspace": "sRGB",
        "connect": ("outColor", ""),
    },
    "BaseColor": {
        "colorspace": "sRGB",
        "connect": ("outColor", "base_color"),
    },
    "BaseColorOpacity": {
        "colorspace": "sRGB",
        "connect": ("outColor", "base_color"),
    },
    "Displacement": {
        "colorspace": "Raw",
        "connect": ("outColor", ""),
    },
    "Emission": {
        "colorspace": "sRGB",
        "connect": ("outColor", "emission_color"),
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
        "connect": ("outColor", ""),
    },
    "Opacity": {
        "colorspace": "Raw",
        "connect": ("outColor", "opacity_color"),
    },
    "Roughness": {
        "colorspace": "Raw",
        "connect": ("outColorR", "refl_roughness"),
    },
    "ScatteringColor": {
        "colorspace": "sRGB",
        "connect": ("outColor", "ms_radius"),
    },
    "SheenColor": {
        "colorspace": "sRGB",
        "connect": ("outColor", "sheen_color"),
    },
    "Translucency": {
        "colorspace": "sRGB",
        "connect": ("outColor", "ms_color"),
    },
    "Transmission": {
        "colorspace": "Raw",
        "connect": ("outColorR", "refr_weight"),
    },
}


class RedshiftMaterial():
    
    # engine_name: str = "Redshift"
    # mat_name: str = None
    # workflow: str = "METALNESS"
    # shading_engine: str = None
    # material: str = None
    # nodes: dict = {}
    
    def __init__(
            self,
            mat_name=""):
        
        self.mat_name = mat_name
        self.engine_name = "Redshift"
        self.workflow = "METALNESS"
        self.shading_engine = None
        self.material = None
        self.nodes = {}
    
    # ------------------------------------------------------------------------------------
    
    def build_material(
            self,
            workflow="",
            tex_maps={}):
        """Function that creates material for Redshift material class.
        
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
        
        self.material = cmds.shadingNode("RedshiftStandardMaterial", asShader=True, name=self.mat_name)
        
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
        
        self._create_uv_node()
        
        return self.material
    
    # ------------------------------------------------------------------------------------
    
    def _connect_basecoloropacity(self):
        """ Connect BaseColorOpacity """
        
        col_node = self.nodes.get("BaseColorOpacity", None)
        if col_node is None:
            return
        
        # ......................................................................
        
        for ch in ["R", "G", "B"]:
            cmds.connectAttr("{}.outAlpha".format(col_node), "{}.opacity_color{}".format(self.material, ch), force=True)
    
    def _create_basecolor_mix(self):
        """ Creates an aiLayerRgba node to mix AO and BaseColor """
        
        col_node = self._get_color_node()
        if col_node is None:
            return
        
        ao_node = self.nodes.get("AmbientOcclusion", None)
        if ao_node is None:
            return
        
        # ......................................................................
        
        self.nodes["AO_Mix"] = mix_node = cmds.shadingNode("RedshiftColorLayer", asTexture=True, name="{}_AO_Mix".format(self.mat_name))
        cmds.setAttr("{}.layer1_mask".format(mix_node), 0)
        cmds.setAttr("{}.layer1_blend_mode".format(mix_node), 1)
        
        cmds.connectAttr("{}.outColor".format(mix_node), "{}.base_color".format(self.material), force=True)
        
        cmds.connectAttr("{}.outColor".format(col_node), "{}.base_color".format(mix_node), force=True)
        cmds.connectAttr("{}.outColor".format(ao_node), "{}.layer1_color".format(mix_node), force=True)
    
    def _create_displacement_setup(self):
        """ Builds a Normal map setup """
        
        displacement_node = self.nodes.get("Displacement", None)
        if displacement_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Displacement_Node"] = disp_node = cmds.shadingNode("RedshiftDisplacement", asShader=True, name="{}_Displacement_Node".format(self.mat_name))
        cmds.setAttr("{}.scale".format(disp_node), 0)
        cmds.connectAttr("{}.out".format(disp_node), "{}.displacementShader".format(self.shading_engine), force=True)
        
        cmds.connectAttr("{}.outColor".format(displacement_node), "{}.texMap".format(disp_node), force=True)
    
    def _create_emission_setup(self):
        """ Builds an Emission map setup """
        
        emission_node = self.nodes.get("Emission", None)
        if emission_node is None:
            return
        
        # ......................................................................
        
        cmds.connectAttr("{}.outColor".format(emission_node), "{}.emission_color".format(self.material), force=True)
        
        cmds.setAttr("{}.emission_weight".format(self.material), 0)
    
    def _create_normal_setup(self):
        """ Builds a Normal map setup """
        
        normal_node = self.nodes.get("Normal", None)
        if normal_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Normal_Node"] = nrm_node = cmds.shadingNode("RedshiftBumpMap", asTexture=True, name="{}_Normal_Node".format(self.mat_name))
        cmds.setAttr("{}.inputType".format(nrm_node), 1)
        cmds.setAttr("{}.scale".format(nrm_node), 1)
        cmds.connectAttr("{}.out".format(nrm_node), "{}.bump_input".format(self.material), force=True)
        cmds.connectAttr("{}.outColor".format(normal_node), "{}.input".format(nrm_node), force=True)
    
    def _create_sheen_setup(self):
        """ Builds a Sheen setup """
        
        sheen_node = self.nodes.get("SheenColor", None)
        if sheen_node is None:
            return
        
        # ......................................................................
        
        cmds.setAttr("{}.sheen_weight".format(self.material), 1)
        cmds.setAttr("{}.sheen_roughness".format(self.material), 0.1)
    
    def _create_subsurface_setup(self):
        """ Builds a Subsurface setup """
        
        sss_node = self.nodes.get("ScatteringColor", None)
        if sss_node is None:
            return
        
        # ......................................................................
        
        col_node = self._get_color_node()
        if col_node is not None:
            cmds.connectAttr("{}.outColor".format(col_node), "{}.ss_scatter_color".format(self.material), force=True)
            
            cmds.connectAttr("{}.outColor".format(col_node), "{}.ms_color".format(self.material), force=True)
        
        # ......................................................................
        
        cmds.setAttr("{}.ms_mode".format(self.material), 2)
        cmds.setAttr("{}.ms_amount".format(self.material), 1)
        cmds.setAttr("{}.ms_radius_scale".format(self.material), 1.0)
    
    def _create_translucency_setup(self):
        """ Builds a Translucency setup """
        
        translucency_node = self.nodes.get("Translucency", None)
        if translucency_node is None:
            return
        
        # ......................................................................
        
        cmds.setAttr("{}.ms_amount".format(self.material), 0.35)
        cmds.setAttr("{}.refr_thin_walled".format(self.material), 1)
    
    def _create_transmission_setup(self):
        """ Builds a Transmission setup """
        
        transmission_node = self.nodes.get("Transmission", None)
        if transmission_node is None:
            return
        
        # ......................................................................
        
        col_node = self._get_color_node()
        if col_node is not None:
            cmds.connectAttr("{}.outColor".format(col_node), "{}.refr_color".format(self.material), force=True)
        
        # ......................................................................
        
        cmds.setAttr("{}.ss_depth".format(self.material), 10)
    
    def _create_uv_node(self):
        """ Adds common UV placement node """
        
        self.nodes["UV"] = uv_node = cmds.shadingNode("place2dTexture", asShader=True, name="{}_UV".format(self.mat_name))
        
        uv_attrs = cmds.listAttr(uv_node, keyable=True)
        
        for image_node in self.nodes.values():
            if "uv" not in cmds.listAttr(image_node):
                continue
            
            cmds.connectAttr("{}.outUV".format(uv_node), "{}.uv".format(image_node), force=True)
            cmds.connectAttr("{}.outUvFilterSize".format(uv_node), "{}.uvFilterSize".format(image_node), force=True)
            
            image_attrs = cmds.listAttr(image_node)
            
            for attr in uv_attrs:
                if attr not in image_attrs:
                    continue
                
                cmds.connectAttr("{}.{}".format(uv_node, attr), "{}.{}".format(image_node, attr), force=True)
    
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
        
        image_node = cmds.shadingNode("file", asTexture=True, name="{}_{}".format(self.mat_name, tex_map))
        
        cmds.setAttr("{}.fileTextureName".format(image_node), file, type="string")
        
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
