from abmatt.brres.mdl0.point import Point


class Normal(Point):
    COMP_COUNT = (3, 9, 3)

    def unpack(self, binfile):
        super(Normal, self).unpack(binfile)
        self.unpack_data(binfile)

    def pack(self, binfile):
        super(Normal, self).pack(binfile)
        self.pack_data(binfile)
