import os
import sys
import time

import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.brres.mdl0 import Mdl0
from abmatt.brres.tex0 import ImgConverter, Tex0, NoImgConverterError
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters.convert_lib import Converter, decode_polygon, \
    Material, combine_matrices
from abmatt.converters.dae import Dae, ColladaNode
from converters.convert_lib import Controller


class DaeConverter2(Converter):

    def load_model(self, model_name=None):
        brres = self.brres
        model_file = self.mdl_file
        cwd = os.getcwd()
        self.bones = {}
        brres_dir, brres_name = os.path.split(brres.name)
        base_name = os.path.splitext(brres_name)[0]
        self.is_map = True if 'map' in base_name else False
        dir, name = os.path.split(model_file)
        if dir:
            os.chdir(dir)  # change to the collada dir to help find relative paths
        AUTO_FIXER.info('Converting {}... '.format(self.mdl_file))
        start = time.time()
        self.dae = dae = Dae(name)
        if not model_name:
            model_name = self.get_mdl0_name(base_name, name)
        self.mdl = mdl = Mdl0(model_name, brres)
        self.__parse_images(dae.get_images(), brres)
        self.__parse_materials(dae.get_materials())
        # geometry
        self.__parse_nodes(dae.get_scene())
        mdl.rebuild_header()
        brres.add_mdl0(mdl)
        if self.is_map:
            mdl.add_map_bones()
        os.chdir(cwd)
        AUTO_FIXER.info('\t... finished in {} secs'.format(round(time.time() - start, 2)))
        return mdl

    def save_model(self, mdl0=None):
        AUTO_FIXER.info('Exporting to {}...'.format(self.mdl_file))
        start = time.time()
        if not mdl0:
            mdl0 = self.brres.models[0]
        cwd = os.getcwd()
        dir, name = os.path.split(self.mdl_file)
        if dir:
            os.chdir(dir)
        base_name, ext = os.path.splitext(name)
        self.image_dir = base_name + '_maps'
        self.texture_library = self.brres.get_texture_map()
        self.tex0_map = {}
        mesh = Dae(initial_scene_name=base_name)
        decoded_mats = [self.__decode_material(x) for x in mdl0.materials]
        # images
        self.__create_image_library(mesh)
        # polygons
        polygons = mdl0.objects
        mesh.add_node(self.__decode_bone(mdl0.bones[0]))
        for polygon in polygons:
            mesh.add_node(self.__decode_geometry(polygon))
        for mat in decoded_mats:
            mesh.add_material(mat)
        os.chdir(cwd)
        mesh.write(self.mdl_file)
        AUTO_FIXER.info('\t...finished in {} seconds.'.format(round(time.time() - start, 2)))

    def __decode_bone(self, mdl0_bone, collada_parent=None):
        name = mdl0_bone.name
        node = ColladaNode(name, {'type': 'JOINT'})
        node.matrix = np.array(mdl0_bone.get_transform_matrix())
        if collada_parent:
            collada_parent.nodes.append(node)
        if mdl0_bone.child:
            self.__decode_bone(mdl0_bone.child, node)
        if mdl0_bone.next:
            self.__decode_bone(mdl0_bone.next, collada_parent)
        return node

    def __decode_geometry(self, polygon):
        name = polygon.name
        node = ColladaNode(name)
        geo = decode_polygon(polygon)
        if geo.colors and self.flags & self.NoColors:
            geo.colors = None
        if geo.normals and self.flags & self.NoNormals:
            geo.normals = None
        node.geometries.append(geo)
        node.controller = get_controller(geo)
        return node

    def __decode_material(self, material):
        diffuse_map = ambient_map = specular_map = None
        for i in range(len(material.layers)):
            layer = material.layers[i].name
            if i == 0:
                diffuse_map = layer
            elif i == 1:
                ambient_map = layer
            elif i == 2:
                specular_map = layer
            if layer not in self.tex0_map:
                tex0 = self.texture_library.get(layer)
                map_path = os.path.join(self.image_dir, layer + '.png')
                self.tex0_map[layer] = (tex0, map_path)
        return Material(material.name, diffuse_map, ambient_map, specular_map, material.xlu * 0.5)

    def __create_image_library(self, mesh):
        if len(self.tex0_map):
            converter = ImgConverter()
            if not converter:
                AUTO_FIXER.error('No image converter found!')
            if not os.path.exists(self.image_dir):
                os.mkdir(self.image_dir)
            os.chdir(self.image_dir)
            for image_name in self.tex0_map:
                tex, path = self.tex0_map[image_name]
                mesh.add_image(image_name, path)
                if not tex:
                    AUTO_FIXER.warn('Missing texture {}'.format(image_name))
                    continue
                if converter:
                    converter.decode(tex, image_name + '.png')

    def __parse_controller(self, controller, matrix):
        bones = controller.bones
        if controller.has_multiple_weights():
            raise self.ConvertError('ERROR: Multiple bone bindings not supported!')
        bone = self.bones[bones[0]]
        self.__encode_geometry(controller.get_bound_geometry(matrix), bone)

    def __encode_geometry(self, geometry, bone=None, matrix=None):
        if matrix is not None and not np.allclose(matrix, self.IDENTITY_MATRIX):
            geometry.apply_matrix(matrix)
        if not self.dae.y_up:
            geometry.swap_y_z_axis()
        if self.flags & self.NoColors:
            geometry.colors = None
        if self.flags & self.NoNormals:
            geometry.normals = None
        geometry.encode(self.mdl, bone)

    def __add_bone(self, node, parent_bone=None, matrix=None):
        name = node.attributes['id']
        self.bones[name] = bone = self.mdl.add_bone(name, parent_bone)
        self.set_bone_matrix(bone, matrix)
        for n in node.nodes:
            self.__add_bone(n, bone, matrix=n.matrix)

    def __parse_nodes(self, nodes, matrix=None):
        for node in nodes:
            matrix = combine_matrices(matrix, node.matrix)
            bone_added = False
            if node.controller:
                self.__parse_controller(node.controller, matrix)
            elif node.geometries:
                for x in node.geometries:
                    self.__encode_geometry(x, matrix=matrix)
            elif node.attributes.get('type') == 'JOINT':
                self.__add_bone(node, matrix=matrix)
                bone_added = True
            if not bone_added:
                self.__parse_nodes(node.nodes, matrix)

    def __parse_materials(self, materials):
        for material in materials:
            material.encode(self.mdl)

    def __parse_images(self, images, brres):
        # images
        self.image_path_map = image_path_map = {}
        try:
            for image in images:
                path = images[image]
                image_path_map[path] = self.try_import_texture(brres, path)
            if not brres.textures and len(images):
                AUTO_FIXER.error('No textures found!')
        except NoImgConverterError as e:
            AUTO_FIXER.error(e)


def get_controller(geometry):
    vert_len = len(geometry.vertices)
    bones = geometry.bones
    bone_names = [x.name for x in bones]
    inv_bind_matrix = np.array([x.get_inv_transform_matrix() for x in bones], np.float)
    bind_matrix = np.array(geometry.linked_bone.get_transform_matrix(), np.float)
    # inv_bind_matrix = np.linalg.inv(bind_matrix)
    weights = np.array([1])
    if geometry.bone_indices is None:
        weight_indices = np.full((vert_len, 2), 0, np.uint)
    else:
        weight_indices = np.stack([geometry.bone_indices, np.full(geometry.bone_indices.shape, 0, np.uint)], -1)
    # weight_indices = np.stack((np.zeros(vert_len, dtype=int), np.arange(1, vert_len + 1, dtype=int)), -1)
    return Controller(geometry.name, bind_matrix, inv_bind_matrix, bone_names, weights,
                      np.full(vert_len, 1, dtype=int), weight_indices, geometry)


def main():
    cmdline_convert(sys.argv[1:], '.dae', DaeConverter2)


if __name__ == '__main__':
    main()
