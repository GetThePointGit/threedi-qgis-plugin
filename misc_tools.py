# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.
"""
Miscellaneous tools.
"""

import logging
import os

from qgis.core import QgsMapLayerRegistry

from .stats.utils import get_csv_layer_cache_files
from .stats.utils import STATS_LAYER_IDENTIFIER
from .utils.user_messages import pop_up_info, pop_up_question
from .utils.layer_from_netCDF import (
    FLOWLINES_LAYER_NAME, NODES_LAYER_NAME, PUMPLINES_LAYER_NAME
)

# Shotgun approach for removing all problematic layers by their layer name.
# Very ad-hoc. Chance that it removes a layer that was not generated by the
# plugin due to filtering-by-name.
IDENTIFIER_LIKE = [
    FLOWLINES_LAYER_NAME,
    NODES_LAYER_NAME,
    PUMPLINES_LAYER_NAME,
    STATS_LAYER_IDENTIFIER,
]

log = logging.getLogger(__name__)


class About(object):
    """Add 3Di logo and about info."""

    def __init__(self, iface):
        self.iface = iface
        self.icon_path = ':/plugins/ThreeDiToolbox/icon.png'
        self.menu_text = "3Di about"

    def run(self):
        """Shows dialog with version information."""
        # todo: add version number and link to sites
        with open(os.path.join(os.path.dirname(__file__),
                  'version.rst'), 'r') as f:
            version = f.readline().rstrip()

        pop_up_info("3Di Tools versie %s" % version,
                    "About", self.iface.mainWindow())

    def on_unload(self):
        pass


class CacheClearer(object):
    """Tool to delete cache files."""

    def __init__(self, iface, ts_datasource):
        """Constructor.

        Args:
            iface: QGIS interface
            ts_datasource: TimeseriesDatasourceModel instance
        """
        self.iface = iface
        self.icon_path = ':/plugins/ThreeDiToolbox/icon_broom.png'
        self.menu_text = "Clear cache"
        self.ts_datasource = ts_datasource

    def run(self):
        """Find cached spatialite and csv layer files for *ALL* items in the
        TimeseriesDatasourceModel (i.e., *ALL* rows) object and delete them.
        """
        spatialite_filepaths = [
            item.spatialite_cache_filepath() for
            item in self.ts_datasource.rows if
            os.path.exists(item.spatialite_cache_filepath())
        ]
        result_dirs = [
            os.path.dirname(item.file_path.value) for
            item in self.ts_datasource.rows
        ]
        csv_filepaths = get_csv_layer_cache_files(*result_dirs)
        # Note: convert to set because duplicates are possible if the same
        # datasource is loaded multiple times
        cached = set(spatialite_filepaths + csv_filepaths)
        if not cached:
            pop_up_info("No cached files found.")
            return

        # Files linked to the layers in the map registry are held open by
        # Windows. You need to delete them manually from the registry to be
        # able to remove the underlying data. Note that deleting the layer
        # from the legend doesn't necessarily delete the layer from the map
        # registry, even though it may appear that no more layers are loaded
        # visually.
        # The specific error message (for googling):
        # error 32 the process cannot access the file because it is being used by another process  # noqa
        all_layers = QgsMapLayerRegistry.instance().mapLayers().values()
        loaded_layers = [
            l for l in all_layers if
            any(identifier in l.name() for identifier in IDENTIFIER_LIKE)
        ]
        loaded_layer_ids = [l.id() for l in loaded_layers]

        yes = pop_up_question(
            "The following files will be deleted:\n" +
            ',\n'.join(cached) +
            "\n\nContinue?"
        )

        if yes:
            try:
                QgsMapLayerRegistry.instance().removeMapLayers(
                    loaded_layer_ids)
            except RuntimeError:
                log.exception("Failed to delete map layer")

            for f in cached:
                try:
                    os.remove(f)
                except OSError:
                    pop_up_info("Failed to delete %s." % f)
            pop_up_info("Cache cleared. You may need to restart QGIS and "
                        "reload your data.")

    def on_unload(self):
        pass
