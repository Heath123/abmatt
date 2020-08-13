"""Tex0 subfile"""
from math import log
import os
from PIL import Image

from brres.lib.binfile import BinFile
from brres.lib.matching import parseValStr, validInt
from brres.subfile import SubFile
from brres.lib.autofix import AUTO_FIXER, Bug


class Tex0(SubFile):
    """ Tex0 Class """
    MAGIC = 'TEX0'
    EXT = 'tex0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}
    EXPECTED_VERSION = 3
    RESIZE_TO_POW_TWO = True
    SETTINGS = ('dimensions', 'format', 'mipmapcount', 'name')
    FORMATS = {0: 'I4', 1: 'I8', 2: 'IA4', 3: 'IA8',
               4: 'RGB565', 5: 'RGB5A3', 6: 'RGBA32',
               8: 'C4', 9: 'C8', 10: 'C14X2', 14: 'CMPR'}

    def __init__(self, name, parent=None, binfile=None):
        super(Tex0, self).__init__(name, parent, binfile)

    def begin(self):
        self.width = 0
        self.height = 0
        self.format = 0
        self.num_images = 0
        self.num_mips = 0
        self.data = None

    def get_str(self, key):
        if key == 'dimensions':
            return self.width, self.height
        elif key == 'format':
            return self.format
        elif key == 'mipmapcount':
            return self.num_mips
        elif key == 'name':
            return self.name

    def set_str(self, key, value):
        if key == 'dimensions':
            vals = parseValStr(value)
            if len(vals) != 2:
                raise ValueError('Expected "width,height" not "{}"'.format(value))
            else:
                return self.set_dimensions(validInt(vals[0], 1), validInt(vals[1], 1))
        elif key == 'format':
            return self.set_format(value)
        elif key == 'mipmapcount':
            return self.set_mipmap_count(validInt(value, 0, 20))
        elif key == 'name':
            return self.set_name(value)

    def set_dimensions(self, width, height):
        if width != self.width or height != self.height:
            ImgConverter().set_dimensions(self, width, height)

    def set_format(self, format):
        if format != self.format:
            ImgConverter().convert(self, format)

    def set_mipmap_count(self, count):
        if count != self.num_mips:
            ImgConverter().set_mipmap_count(self, count)

    def set_name(self, name):
        return self.parent.rename_texture(self, name)

    @staticmethod
    def is_power_of_two(n):
        return n & (n - 1) == 0

    @staticmethod
    def nearest_power_of_two(v):
        return pow(2, round(log(v) / log(2)))

    def set_power_of_two(self):
        width = self.width if self.is_power_of_two(self.width) else self.nearest_power_of_two(self.width)
        height = self.height if self.is_power_of_two(self.height) else self.nearest_power_of_two(self.height)
        self.set_dimensions(width, height)

    def paste(self, item):
        self.width = item.width
        self.height = item.height
        self.format = item.format
        self.num_images = item.num_images
        self.num_mips = item.num_mips
        self.data = item.data

    def check(self):
        super(Tex0, self).check()
        if not self.is_power_of_two(self.width) or not self.is_power_of_two(self.height):
            b = Bug(2, 2, 'TEX0 {} not a power of 2'.format(self.name), 'Resize Tex0')
            if self.RESIZE_TO_POW_TWO:
                self.set_power_of_two()
                b.resolve()

    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.width, self.height, self.format, self.num_images, _, self.num_mips, _ = binfile.read('I2H3IfI', 0x1c)
        binfile.recall()
        self.data = binfile.readRemaining(self.byte_len)
        binfile.end()

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('I2H3IfI', 0, self.width, self.height, self.format, self.num_images, 0, self.num_mips, 0)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(self.data)
        binfile.end()

    def info(self, key=None, indentation=0):
        print('{} {}: {} {}x{} mips:{}'.format(self.MAGIC, self.name, self.FORMATS[self.format],
                                               self.width, self.height, self.num_mips))


def which(program):
    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, program)
        if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
            return exe_file


class EncodeError(Exception):
    def __init__(self, msg=None):
        super(EncodeError, self).__init__(msg)


class DecodeError(Exception):
    def __init__(self, msg=None):
        super(DecodeError, self).__init__(msg)


class NoImgConverterError(Exception):
    def __init__(self, msg=None):
        super(NoImgConverterError, self).__init__(msg)


class ImgConverterI:
    def __init__(self, converter):
        self.converter = converter

    def encode(self, img_file, tex_format, num_mips=-1):
        raise NotImplementedError()

    def decode(self, tex0, dest_file):
        raise NotImplementedError()

    def convert(self, tex0, tex_format):
        raise NotImplementedError()

    def set_mipmap_count(self, tex0, mip_count):
        raise NotImplementedError()

    def set_dimensions(self, tex0, width, height):
        raise NotImplementedError()

    def __bool__(self):
        return self.converter


class ImgConverter:
    INSTANCE = None  # singleton instance

    def __init__(self, converter=None):
        if not self.INSTANCE:
            if not converter:
                converter = self.Wimgt()
            self.INSTANCE = converter
        elif converter:
            self.INSTANCE.converter = converter

    class Wimgt(ImgConverterI):
        def __init__(self):
            program = 'wimgt'
            if which(program):
                self.temp_dest = 'tmp.tex0'
            else:
                program = None
            super(ImgConverter.Wimgt, self).__init__(program)

        def encode(self, img_file, tex_format, num_mips=-1):
            # encode
            dir, fname = os.path.split(img_file)
            name = os.path.splitext(fname)[0]
            mips = str(num_mips) if num_mips >= 0 else 'auto'
            result = os.system(
                '{} encode {} -d {} -x {} --n-mm={} -o'.format(self.converter, img_file, self.temp_dest, tex_format,
                                                               mips))
            if result:
                raise EncodeError()
            t = Tex0(name, BinFile(self.temp_dest))
            os.remove(self.temp_dest)
            t.name = name
            return t

        def decode(self, tex0, dest_file):
            if not dest_file:
                dest_file = tex0.name + '.png'
            elif os.path.isdir(dest_file):
                dest_file = os.path.join(dest_file, tex0.name + '.png')
            f = BinFile(self.temp_dest, 'w')
            tex0.pack(f)
            f.commitWrite()
            result = os.system('{} decode {} -d {} -o'.format(self.converter, self.temp_dest, dest_file))
            os.remove(self.temp_dest)
            if result:
                raise DecodeError()
            return dest_file

        def convert(self, tex0, tex_format):
            f = BinFile(self.temp_dest, 'w')
            tex0.pack(f)
            f.commitWrite()
            result = os.system('{} encode {} -o -x {}'.format(self.converter, self.temp_dest, tex_format))
            if result:
                raise EncodeError()
            t = Tex0(tex0.name, tex0.parent, BinFile(self.temp_dest))
            os.remove(self.temp_dest)
            return t

        def set_mipmap_count(self, tex0, mip_count=-1):
            fname = self.decode(tex0, self.temp_dest)
            tex = self.encode(fname, tex0.format, mip_count)
            tex0.paste(tex)

        def set_dimensions(self, tex0, width, height):
            fname = self.decode(tex0, self.temp_dest)
            im = Image.open(fname)
            im.resize(width, height)
            im.save(fname)
            tex = self.encode(fname, tex0.format)
            tex0.paste(tex)

    def __getattr__(self, item):
        if not self.INSTANCE:
            raise NoImgConverterError()
        return getattr(self.INSTANCE, item)

    def __bool__(self):
        return bool(self.INSTANCE)