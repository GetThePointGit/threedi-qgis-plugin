# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.

import logging
from sqlalchemy import update

from ThreeDiToolbox.sql_models.model_schematisation import (
    ConnectionNode, Manhole,
    BoundaryCondition1D, Pipe, Pumpstation, )
from ThreeDiToolbox.sql_models.constants import Constants


log = logging.getLogger(__name__)


class Guesser(object):

    def __init__(self, threedi_database):
        self.db = threedi_database

    def run(self, checks, only_empty_fields=True):

        self.db.create_and_check_fields()
        session = self.db.get_session()

        msg = ''
        if 'manhole_indicator' in checks:
            manhole_update_count = 0

            up = update(Manhole).\
                where(Manhole.connection_node_id ==
                      Pumpstation.connection_node_start_id).\
                values(manhole_indicator=Constants.MANHOLE_INDICATOR_PUMPSTATION)
            if only_empty_fields:
                up = up.where(Manhole.manhole_indicator == None)
            ret = session.execute(up)
            manhole_update_count += ret.rowcount

            up = update(Manhole).\
                where(Manhole.connection_node_id == BoundaryCondition1D.connection_node_id).\
                values(manhole_indicator=Constants.MANHOLE_INDICATOR_OUTLET)
            if only_empty_fields:
                up = up.where(Manhole.manhole_indicator == None)
            ret = session.execute(up)
            manhole_update_count += ret.rowcount

            up = update(Manhole). \
                where(Manhole.manhole_indicator == None). \
                values(manhole_indicator=Constants.MANHOLE_INDICATOR_MANHOLE)
            if only_empty_fields:
                up = up.where(Manhole.manhole_indicator == None)
            ret = session.execute(up)
            manhole_update_count += ret.rowcount

            msg += 'Manhole indicator updated {0} manholes. '.format(manhole_update_count)

        if 'pipe_friction' in checks:
            pipe_friction_count = 0

            table_manning = {
                (Constants.MATERIAL_TYPE_CONCRETE, 0.0145),
                (Constants.MATERIAL_TYPE_PVC, 0.0110),
                (Constants.MATERIAL_TYPE_STONEWARE, 0.0115),
                (Constants.MATERIAL_TYPE_CAST_IRON, 0.0135),
                (Constants.MATERIAL_TYPE_BRICKWORK, 0.0160),
                (Constants.MATERIAL_TYPE_HPE, 0.0110),
                (Constants.MATERIAL_TYPE_HPDE, 0.0110),
                (Constants.MATERIAL_TYPE_SHEET_IRON, 0.0135),
                (Constants.MATERIAL_TYPE_STEEL, 0.0130),
            }

            for material_code, friction in table_manning:
                up = update(Pipe). \
                    where(Pipe.material == material_code). \
                    values(friction_value=friction,
                           friction_type=Constants.FRICTION_TYPE_MANNING)
                if only_empty_fields:
                    up = up.where(Pipe.friction_value == None)

                ret = session.execute(up)
                pipe_friction_count += ret.rowcount

            msg += 'Pipe friction updated {0} pipes. '.format(pipe_friction_count)

        if 'manhole_area' in checks:
            manhole_area_count = 0

            # todo: differentiate on the shape
            up = update(ConnectionNode). \
                where(ConnectionNode.id == Manhole.connection_node_id). \
                where(ConnectionNode.storage_area == None). \
                where(Manhole.length == None). \
                where(Manhole.width != None). \
                values(storage_area=Manhole.width * Manhole.width)
            ret = session.execute(up)
            manhole_area_count += ret.rowcount

            up = update(ConnectionNode). \
                where(ConnectionNode.id == Manhole.connection_node_id). \
                where(ConnectionNode.storage_area == None). \
                where(Manhole.length != None). \
                where(Manhole.width != None). \
                values(storage_area=Manhole.width * Manhole.length)
            ret = session.execute(up)
            manhole_area_count += ret.rowcount

            msg += 'Manhole area updated {0} manholes. '.format(manhole_area_count)

        return msg