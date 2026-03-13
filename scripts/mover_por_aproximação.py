from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterField,
    QgsSpatialIndex,
    QgsDistanceArea
)


class MoverParaEstrutura(QgsProcessingAlgorithm):

    ORIGEM = "ORIGEM"
    DESTINO = "DESTINO"
    MODO = "MODO"
    DIST = "DIST"
    MAX_TESTE = "MAX_TESTE"
    CAMPO_BARR = "CAMPO_BARR"

    def name(self):
        return "mover_por_aproximação"

    def displayName(self):
        return "Mover Por Aproximação"

    def group(self):
        return "Spatial Tools"

    def groupId(self):
        return "spatial_tools"

    def createInstance(self):
        return MoverParaEstrutura()

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ORIGEM,
                "Camada origem"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DESTINO,
                "Camada destino"
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.MODO,
                "Modo de operação",
                options=["POSTE (1:1)", "IP (por barramento)"],
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_BARR,
                "Campo barramento (usado no modo IP)",
                parentLayerParameterName=self.ORIGEM,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIST,
                "Distância máxima (metros)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_TESTE,
                "Máx destinos testados",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=3
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        origem = self.parameterAsSource(parameters, self.ORIGEM, context)
        destino = self.parameterAsSource(parameters, self.DESTINO, context)

        modo = self.parameterAsEnum(parameters, self.MODO, context)
        campo_barr = self.parameterAsString(parameters, self.CAMPO_BARR, context)

        dist_max = self.parameterAsDouble(parameters, self.DIST, context)
        max_test = self.parameterAsInt(parameters, self.MAX_TESTE, context)

        feedback.pushInfo("Criando Spatial Index...")

        index_origem = QgsSpatialIndex(origem.getFeatures())
        index_destino = QgsSpatialIndex(destino.getFeatures())

        destino_dict = {f.id(): f for f in destino.getFeatures()}

        dist_calc = QgsDistanceArea()
        dist_calc.setSourceCrs(origem.sourceCrs(), context.transformContext())
        dist_calc.setEllipsoid("WGS84")

        destino_ocupado = {}
        mudancas = {}

        total = origem.featureCount()

        for i, feat in enumerate(origem.getFeatures()):

            if feedback.isCanceled():
                break

            feedback.setProgress(int(i / total * 100))

            geom_origem = feat.geometry()

            ids_destino = index_destino.nearestNeighbor(
                geom_origem,
                max_test
            )

            for dest_id in ids_destino:

                dest_feat = destino_dict[dest_id]
                geom_dest = dest_feat.geometry()

                ponto_prox = geom_dest.nearestPoint(geom_origem)

                dist_m = dist_calc.measureLine(
                    geom_origem.asPoint(),
                    ponto_prox.asPoint()
                )

                if dist_m > dist_max:
                    continue

                # ------------------------------
                # MODO POSTE
                # ------------------------------

                if modo == 0:

                    id_reverso = index_origem.nearestNeighbor(
                        geom_dest,
                        1
                    )[0]

                    if id_reverso == feat.id():

                        if dest_id not in destino_ocupado:

                            destino_ocupado[dest_id] = feat.id()
                            mudancas[feat.id()] = geom_dest
                            break

                # ------------------------------
                # MODO IP
                # ------------------------------

                else:

                    barr = feat[campo_barr]

                    if barr is None or str(barr).strip() == "":
                        continue

                    if dest_id not in destino_ocupado:

                        destino_ocupado[dest_id] = barr
                        mudancas[feat.id()] = geom_dest
                        break

                    elif destino_ocupado[dest_id] == barr:

                        mudancas[feat.id()] = geom_dest
                        break

        layer = context.getMapLayer(origem.sourceName())

        if mudancas:

            layer.startEditing()
            layer.beginEditCommand("Mover feições automaticamente")

            for fid, geom in mudancas.items():

                layer.changeGeometry(fid, geom)

            layer.endEditCommand()

        feedback.pushInfo(f"Movidos: {len(mudancas)}")

        return {}