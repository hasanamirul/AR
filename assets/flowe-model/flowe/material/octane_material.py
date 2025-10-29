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


# NOTE : supports Octane v 2020.1.0+


from .materials import (
    filter_tex_maps,
)

import maya.cmds as cmds


TEX_MAP_ATTRS = {
    "AmbientOcclusion": {
        "gamma": 2.2,
        "connect": ("outTex", ""),
    },
    "BaseColor": {
        "gamma": 2.2,
        "connect": ("outTex", "Albedo"),
    },
    "BaseColorOpacity": {
        "gamma": 2.2,
        "connect": ("outTex", "Albedo"),
    },
    "Displacement": {
        "gamma": 1,
        "connect": ("outTex", ""),
    },
    "Emission": {
        "gamma": 2.2,
        "connect": ("outTex", ""),
    },
    "MaskMap": {
        "gamma": 1,
        "connect": ("outTex", ""),
    },
    "Metallic": {
        "gamma": 1,
        "connect": ("outTex", "Metallic"),
    },
    "Normal": {
        "gamma": 1,
        "connect": ("outTex", "Normal"),
    },
    "Opacity": {
        "gamma": 1,
        "connect": ("outTex", "Opacity"),
    },
    "Roughness": {
        "gamma": 1,
        "connect": ("outTex", "Roughness"),
    },
    "ScatteringColor": {
        "gamma": 1,
        "connect": ("outTex", ""),
    },
    "SheenColor": {
        "gamma": 2.2,
        "connect": ("outTex", "Sheen"),
    },
    "Translucency": {
        "gamma": 2.2,
        "connect": ("outTex", ""),
    },
    "Transmission": {
        "gamma": 1,
        "connect": ("outTex", "Transmission"),
    },
}


class OctaneMaterial():
    
    # engine_name: str = "Octane"
    # mat_name: str = None
    # workflow: str = "METALNESS"
    # shading_engine: str = None
    # material: str = None
    # nodes: dict = {}
    
    def __init__(
            self,
            mat_name=""):
        
        self.mat_name = mat_name
        self.engine_name = "Octane"
        self.workflow = "METALNESS"
        self.shading_engine = None
        self.material = None
        self.nodes = {}
    
    # ------------------------------------------------------------------------------------
    
    def build_material(
            self,
            workflow="",
            tex_maps={}):
        """Function that creates material for Octane material class.
        
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
        
        self.material = cmds.shadingNode("octaneUniversalMaterial", asShader=True, name=self.mat_name)
        
        cmds.connectAttr("{}.outColor".format(self.material), "{}.surfaceShader".format(self.shading_engine), force=True)
        
        cmds.setAttr("{}.TransmissionType".format(self.material), 1)
        cmds.setAttr("{}.BsdfModel".format(self.material), 2)
        
        self.nodes = {}
        
        for tex_map, file in tex_maps.items():
            self.nodes[tex_map] = image_node = self._create_image_node(tex_map, file)
            
            self._connect_image_node(tex_map, image_node, self.material)
        
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
    
    def _create_basecolor_mix(self):
        """ Creates an aiLayerRgba node to mix AO and BaseColor """
        
        col_node = self._get_color_node()
        if col_node is None:
            return {}
        
        ao_node = self.nodes.get("AmbientOcclusion", None)
        if ao_node is None:
            return {}
        
        # ......................................................................
        
        # RGB Spectrum node
        self.nodes["AO_Base"] = rgb_node = cmds.shadingNode("octaneRGBSpectrumTexture", asTexture=True, name="{}_AO_Base".format(self.mat_name))
        cmds.setAttr("{}.inColor".format(rgb_node), 1, 1, 1, type="double3")
        
        # Mix value node
        self.nodes["AO_Strength"] = mix_value = cmds.shadingNode("octaneFloatTexture", asTexture=True, name="{}_AO_Strength".format(self.mat_name))
        cmds.setAttr("{}.Value".format(mix_value), 0)
        
        # Mix AO + RGB Spectrum
        self.nodes["AO_Mix"] = mix_node = cmds.shadingNode("octaneMixTexture", asTexture=True, name="{}_AO_Mix".format(self.mat_name))
        cmds.connectAttr("{}.outTex".format(mix_value), "{}.Amount".format(mix_node), force=True)
        cmds.connectAttr("{}.outTex".format(rgb_node), "{}.Texture1".format(mix_node), force=True)
        cmds.connectAttr("{}.outTex".format(ao_node), "{}.Texture2".format(mix_node), force=True)
        
        # Multiply Mix + Color
        self.nodes["AO_Multiply"] = mult_node = cmds.shadingNode("octaneMultiplyTexture", asTexture=True, name="{}_AO_Multiply".format(self.mat_name))
        cmds.connectAttr("{}.outTex".format(col_node), "{}.Texture1".format(mult_node), force=True)
        cmds.connectAttr("{}.outTex".format(mix_node), "{}.Texture2".format(mult_node), force=True)
        
        # Multiply to self.material
        cmds.connectAttr("{}.outTex".format(mult_node), "{}.Albedo".format(self.material), force=True)
    
    def _create_displacement_setup(self):
        """ Builds a Displacement map setup """
        
        displacement_node = self.nodes.get("Displacement", None)
        if displacement_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Displacement_Node"] = disp_node = cmds.shadingNode("octaneDisplacementNode", asTexture=True, name="{}_Displacement_Node".format(self.mat_name))
        cmds.setAttr("{}.Height".format(disp_node), 0)
        cmds.connectAttr("{}.outDisp".format(disp_node), "{}.Displacement".format(self.material), force=True)
        cmds.connectAttr("{}.outTex".format(displacement_node), "{}.Texture".format(disp_node), force=True)
    
    def _create_emission_setup(self):
        """ Builds an Emission map setup """
        
        emission_node = self.nodes.get("Emission", None)
        if emission_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Emission_Node"] = emiss_node = cmds.shadingNode("octaneTextureEmission", asTexture=True, name="{}_Emission_Node".format(self.mat_name))
        cmds.setAttr("{}.Power".format(emiss_node), 0)
        cmds.setAttr("{}.SurfaceBrightness".format(emiss_node), 1)
        cmds.connectAttr("{}.outEmission".format(emiss_node), "{}.Emission".format(self.material), force=True)
        cmds.connectAttr("{}.outTex".format(emission_node), "{}.Efficiency".format(emiss_node), force=True)
    
    def _create_normal_setup(self):
        """ Builds a Normal map setup """
        
        normal_node = self.nodes.get("Normal", None)
        if normal_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Normal_Invert"] = invert_node = cmds.shadingNode("octaneChannelInvertTexture", asTexture=True, name="{}_Normal_Invert".format(self.mat_name))
        cmds.connectAttr("{}.outTex".format(invert_node), "{}.Normal".format(self.material), force=True)
        cmds.connectAttr("{}.outTex".format(normal_node), "{}.input".format(invert_node), force=True)
    
    def _create_sheen_setup(self):
        """ Builds a Sheen setup """
        
        sheen_node = self.nodes.get("SheenColor", None)
        if sheen_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Sheen_Strength"] = sheen_value = cmds.shadingNode("octaneFloatTexture", asTexture=True, name="{}_Sheen_Strength".format(self.mat_name))
        cmds.setAttr("{}.Value".format(sheen_value), 0.1)
        cmds.connectAttr("{}.outTex".format(sheen_value), "{}.SheenRoughness".format(self.mat_name), force=True)
    
    def _create_subsurface_setup(self):
        """ Builds a Subsurface setup """
        
        sss_node = self.nodes.get("ScatteringColor", None)
        if sss_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Scattering_Medium"] = medium_node = cmds.shadingNode("octaneScatteringMedium", asTexture=True, name="{}_Scattering_Medium".format(self.mat_name))
        cmds.setAttr("{}.Scale".format(medium_node), 100)
        cmds.connectAttr("{}.outMedium".format(medium_node), "{}.Medium".format(self.material), force=True)
        cmds.connectAttr("{}.outTex".format(sss_node), "{}.Scattering".format(medium_node), force=True)
        
        # ......................................................................
        
        col_node = self._get_color_node()
        
        if col_node is not None:
            cmds.connectAttr("{}.outTex".format(col_node), "{}.Absorption".format(medium_node), force=True)
            
            self.nodes["Color_Correct"] = cc_node = cmds.shadingNode("octaneColorCorrectTexture", asTexture=True, name="{}_Color_Correct".format(self.mat_name))
            cmds.setAttr("{}.Exposure".format(cc_node), 10)
            cmds.connectAttr("{}.outTex".format(cc_node), "{}.Transmission".format(self.material), force=True)
            cmds.connectAttr("{}.outTex".format(col_node), "{}.octTexture".format(cc_node), force=True)
    
    def _create_translucency_setup(self):
        """ Builds a Translucency setup """
        
        translucency_node = self.nodes.get("Translucency", None)
        if translucency_node is None:
            return
        
        # ......................................................................
        
        self.nodes["Translucency_Float"] = float_node = cmds.shadingNode("octaneFloatTexture", asTexture=True, name="{}_Translucency_Float".format(self.mat_name))
        cmds.setAttr("{}.Value".format(float_node), 0.35)
        
        # ......................................................................
        
        self.nodes["Translucency_Invert"] = invert_node = cmds.shadingNode("octaneInvertTexture", asTexture=True, name="{}_Translucency_Invert".format(self.mat_name))
        
        col_node = self.nodes.get("AO_Multiply", None)
        if col_node is None:
            col_node = self._get_color_node()
        
        self.nodes["Color_Multiply"] = col_mult = cmds.shadingNode("octaneMultiplyTexture", asTexture=True, name="{}_Color_Multiply".format(self.mat_name))
        cmds.connectAttr("{}.outTex".format(col_node), "{}.Texture1".format(col_mult), force=True)
        cmds.connectAttr("{}.outTex".format(invert_node), "{}.Texture2".format(col_mult), force=True)
        cmds.connectAttr("{}.outTex".format(col_mult), "{}.Albedo".format(self.material), force=True)
        
        # ......................................................................
        
        self.nodes["Translucency_Multiply"] = mult_node = cmds.shadingNode("octaneMultiplyTexture", asTexture=True, name="{}_Translucency_Multiply".format(self.mat_name))
        cmds.connectAttr("{}.outTex".format(translucency_node), "{}.Texture1".format(mult_node), force=True)
        cmds.connectAttr("{}.outTex".format(float_node), "{}.Texture2".format(mult_node), force=True)
        cmds.connectAttr("{}.outTex".format(mult_node), "{}.Transmission".format(self.material), force=True)
    
    def _create_transmission_setup(self):
        """ Builds a Transmission setup """
        
        transmission_node = self.nodes.get("Transmission", None)
        if transmission_node is None:
            return
        
        # ......................................................................
        
        self.shading_engine = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="{}_Mix_SG".format(self.mat_name))
        
        self.nodes["Specular_Mat"] = spec_mat = cmds.shadingNode("octaneUniversalMaterial", asShader=True, name="{}_Specular".format(self.mat_name))
        cmds.setAttr("{}.TransmissionType".format(spec_mat), 0)
        cmds.setAttr("{}.BsdfModel".format(spec_mat), 2)
        
        self.nodes["Transmission_Mix"] = mat_mix = cmds.shadingNode("octaneMixMaterial", asTexture=True, name="{}_Mix".format(self.mat_name))
        
        cmds.connectAttr("{}.outTex".format(transmission_node), "{}.Amount".format(mat_mix), force=True)
        cmds.connectAttr("{}.outTex".format(transmission_node), "{}.Transmission".format(spec_mat), force=True)
        
        cmds.connectAttr("{}.outMaterial".format(spec_mat), "{}.Material1".format(mat_mix), force=True)
        cmds.connectAttr("{}.outMaterial".format(self.material), "{}.Material2".format(mat_mix), force=True)
        
        cmds.connectAttr("{}.outColor".format(mat_mix), "{}.surfaceShader".format(self.shading_engine), force=True)
        
        # ......................................................................
        
        self.nodes["Albedo"] = albedo_node = cmds.shadingNode("octaneRGBSpectrumTexture", asTexture=True, name="{}_Albedo".format(self.mat_name))
        cmds.setAttr("{}.inColor".format(albedo_node), 0, 0, 0, type="double3")
        
        cmds.connectAttr("{}.outTex".format(albedo_node), "{}.Albedo".format(spec_mat), force=True)
        
        # ......................................................................
        
        col_node = self._get_color_node()
        
        if col_node is not None:
            self.nodes["Absorption"] = medium_node = cmds.shadingNode("octaneAbsorptionMedium", asTexture=True, name="{}_Absorption".format(self.mat_name))
            cmds.setAttr("{}.Scale".format(medium_node), 100)
            cmds.connectAttr("{}.outMedium".format(medium_node), "{}.Medium".format(self.material), force=True)
            cmds.connectAttr("{}.outTex".format(col_node), "{}.Absorption".format(medium_node), force=True)
        
        # ......................................................................
        
        for tex_map in ["Metallic", "Roughness", "Opacity", "Normal"]:
            image_node = self.nodes.get(tex_map, None)
            if image_node is None:
                continue
            
            self._connect_image_node(tex_map, image_node, spec_mat)
    
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
            file="",
            node_type="octaneImageTexture"):
        """ Creates an Image node,
        sets the filename path,
        sets the node gamma
        """
        
        image_node = cmds.shadingNode(node_type, asTexture=True, name="{}_{}".format(self.mat_name, tex_map))
        
        cmds.setAttr("{}.File".format(image_node), file, type="string")
        
        gamma = TEX_MAP_ATTRS.get(tex_map, {}).get("gamma", 1)
        cmds.setAttr("{}.Gamma".format(image_node), gamma)
        
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
