import processing

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingException,
    QgsSpatialIndex,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsFields,
    QgsWkbTypes
)


class TargetDetector(QgsProcessingAlgorithm):

    POSTES = 'POSTES'
    IP = 'IP'
    BT = 'BT'
    OUTPUT = 'OUTPUT'

    DIST_IP = 'DIST_IP'
    DIST_BT = 'DIST_BT'
    DIST_CLUSTER = 'DIST_CLUSTER'
    BUFFER_EXTERNO = 'BUFFER_EXTERNO'
    AREA_MIN = 'AREA_MIN'

    BUFFER_IP = 'BUFFER_IP'
    BUFFER_FLY = 'BUFFER_FLY'

    # -------------------------------------------------

    def name(self):
        return "target_detector"

    def displayName(self):
        return "Detector de Alvos"

    def group(self):
        return "Spatial Tools"

    def groupId(self):
        return "spatial_tools"

    def createInstance(self):
        return TargetDetector()

    # -------------------------------------------------

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POSTES,
                "Postes"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IP,
                "Iluminação pública"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BT,
                "Rede BT"
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIST_IP,
                "Distância mínima IP",
                defaultValue=8
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIST_BT,
                "Distância máxima BT",
                defaultValue=30
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIST_CLUSTER,
                "Metade do lado do quadrado",
                defaultValue=30
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFFER_EXTERNO,
                "Buffer externo (arredondar)",
                defaultValue=10
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFFER_IP,
                "Buffer IP (buraco)",
                defaultValue=2
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFFER_FLY,
                "Buffer FlyTap",
                defaultValue=2
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.AREA_MIN,
                "Área mínima",
                defaultValue=600
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Polígonos alvo"
            )
        )

    # -------------------------------------------------

    def reprojetar(self, layer, context):

        return processing.run(
            "native:reprojectlayer",
            {
                'INPUT': layer,
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3857'),
                'OUTPUT': 'memory:'
            },
            context=context
        )['OUTPUT']

    # -------------------------------------------------

    def quadrado(self, ponto, d):

        x = ponto.x()
        y = ponto.y()

        return QgsGeometry.fromPolygonXY([[

            QgsPointXY(x-d, y-d),
            QgsPointXY(x+d, y-d),
            QgsPointXY(x+d, y+d),
            QgsPointXY(x-d, y+d),
            QgsPointXY(x-d, y-d)

        ]])

    # -------------------------------------------------

    def processAlgorithm(self, parameters, context, feedback):

        postes = self.parameterAsVectorLayer(parameters, self.POSTES, context)
        ip = self.parameterAsVectorLayer(parameters, self.IP, context)
        bt = self.parameterAsVectorLayer(parameters, self.BT, context)

        dist_ip = self.parameterAsDouble(parameters, self.DIST_IP, context)
        dist_bt = self.parameterAsDouble(parameters, self.DIST_BT, context)
        dist_cluster = self.parameterAsDouble(parameters, self.DIST_CLUSTER, context)
        buffer_externo = self.parameterAsDouble(parameters, self.BUFFER_EXTERNO, context)
        buffer_ip = self.parameterAsDouble(parameters, self.BUFFER_IP, context)
        buffer_fly = self.parameterAsDouble(parameters, self.BUFFER_FLY, context)
        area_min = self.parameterAsDouble(parameters, self.AREA_MIN, context)

        feedback.pushInfo("Reprojetando camadas")

        postes = self.reprojetar(postes, context)
        ip = self.reprojetar(ip, context)
        bt = self.reprojetar(bt, context)

        # -------------------------------------------------
        # Índices espaciais
        # -------------------------------------------------

        idx_ip = QgsSpatialIndex(
            ip.getFeatures(),
            flags=QgsSpatialIndex.FlagStoreFeatureGeometries
        )

        idx_bt = QgsSpatialIndex(
            bt.getFeatures(),
            flags=QgsSpatialIndex.FlagStoreFeatureGeometries
        )

        # -------------------------------------------------
        # Máscara FlyTap
        # -------------------------------------------------

        buffers_fly = []

        for f in postes.getFeatures():

            tipo = f['Tipo']

            if tipo and 'FLY' in str(tipo).upper():
                buffers_fly.append(f.geometry().buffer(buffer_fly, 8))

        mascara_fly = QgsGeometry.unaryUnion(buffers_fly) if buffers_fly else None

        feedback.pushInfo("Máscara FlyTap criada")

        # -------------------------------------------------
        # Filtro de postes válidos
        # -------------------------------------------------

        postes_validos = []

        for f in postes.getFeatures():

            g = f.geometry()

            tipo = f['Tipo']

            if tipo and 'FLY' in str(tipo).upper():
                continue

            nearest_ip = idx_ip.nearestNeighbor(g.asPoint(), 1)

            tem_ip = False

            if nearest_ip:

                geom_ip = idx_ip.geometry(nearest_ip[0])

                if g.distance(geom_ip) <= dist_ip:
                    tem_ip = True

            if tem_ip:
                continue

            nearest_bt = idx_bt.nearestNeighbor(g.asPoint(), 1)

            tem_bt = False

            if nearest_bt:

                geom_bt = idx_bt.geometry(nearest_bt[0])

                if g.distance(geom_bt) <= dist_bt:
                    tem_bt = True

            if not tem_bt:
                continue

            postes_validos.append(g)

        feedback.pushInfo(f"Postes válidos: {len(postes_validos)}")

        # -------------------------------------------------
        # Clusters
        # -------------------------------------------------

        buffers_postes = []

        for g in postes_validos:

            quad = self.quadrado(g.asPoint(), dist_cluster)
            buffers_postes.append(quad)

        uniao_postes = QgsGeometry.unaryUnion(buffers_postes)

        if uniao_postes.isMultipart():
            grupos = uniao_postes.asGeometryCollection()
        else:
            grupos = [uniao_postes]

        feedback.pushInfo(f"Clusters criados: {len(grupos)}")

        # -------------------------------------------------
        # Máscara IP
        # -------------------------------------------------

        buffers_ip = []

        for f in ip.getFeatures():
            buffers_ip.append(f.geometry().buffer(buffer_ip, 8))

        mascara_ip = QgsGeometry.unaryUnion(buffers_ip) if buffers_ip else None

        feedback.pushInfo("Máscara de IP criada")

        # -------------------------------------------------
        # Polígonos finais
        # -------------------------------------------------

        poligonos = []

        for geom in grupos:

            if not geom or not geom.isGeosValid():
                continue

            geom = geom.buffer(buffer_externo, 8)

            if mascara_ip and not mascara_ip.isEmpty():
                geom = geom.difference(mascara_ip)

            if mascara_fly and not mascara_fly.isEmpty():
                geom = geom.difference(mascara_fly)

            if not geom or geom.isEmpty():
                continue

            if geom.area() < area_min:
                continue

            if geom.isMultipart():

                for parte in geom.asGeometryCollection():

                    if parte.area() >= area_min:
                        poligonos.append(parte)

            else:

                poligonos.append(geom)

        feedback.pushInfo(f"Polígonos finais: {len(poligonos)}")

        # -------------------------------------------------
        # OUTPUT
        # -------------------------------------------------

        fields = QgsFields()

        (sink, sink_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Polygon,
            QgsCoordinateReferenceSystem('EPSG:3857')
        )

        for g in poligonos:

            f = QgsFeature(fields)
            f.setGeometry(g)

            sink.addFeature(f)

        return {self.OUTPUT: sink_id}