# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterField,
    QgsFeatureSink,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsSpatialIndex,
    QgsDistanceArea,
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes,
    QgsGeometry
)


class SelecaoPontosIsolados(QgsProcessingAlgorithm):

    CAMADA_BUSCA = 'CAMADA_BUSCA'
    CAMADA_REFERENCIA = 'CAMADA_REFERENCIA'
    RAIO = 'RAIO'
    CRIAR_CAMADA = 'CRIAR_CAMADA'
    CAMADA_SAIDA = 'CAMADA_SAIDA'

    CAMPO_MUNICIPIO = "CAMPO_MUNICIPIO"
    CAMPO_MSLINK = "CAMPO_MSLINK"
    CAMPO_BARRAMENTO = "CAMPO_BARRAMENTO"

    def name(self):
        return 'selecao_pontos_isolados'

    def displayName(self):
        return 'Seleção de Pontos Isolados (Métrico)'

    def group(self):
        return "Spatial Tools"

    def groupId(self):
        return "spatial_tools"

    def createInstance(self):
        return SelecaoPontosIsolados()

    def shortHelpString(self):
        return """
Seleciona pontos que não possuem vizinhos dentro do raio especificado.

Diferenciais:
• Spatial Index (R-Tree)
• cálculo geodésico em metros
• saída opcional padronizada
• campos configuráveis
"""

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_BUSCA,
                'Camada de busca',
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_REFERENCIA,
                'Camada de referência',
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RAIO,
                'Raio de busca (metros)',
                QgsProcessingParameterNumber.Double,
                defaultValue=1.0
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_MUNICIPIO,
                "Campo município",
                parentLayerParameterName=self.CAMADA_BUSCA
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_MSLINK,
                "Campo mslink_pg",
                parentLayerParameterName=self.CAMADA_BUSCA
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_BARRAMENTO,
                "Campo barramento",
                parentLayerParameterName=self.CAMADA_BUSCA
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CRIAR_CAMADA,
                'Criar camada de saída',
                defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.CAMADA_SAIDA,
                'Camada saída (EPSG:4326)',
                optional=True
            )
        )

    # -----------------------------------------------------

    def get_point(self, geom):

        if geom.isMultipart():
            return geom.asMultiPoint()[0]

        return geom.asPoint()

    # -----------------------------------------------------

    def processAlgorithm(self, parameters, context, feedback):

        camada_busca = self.parameterAsVectorLayer(parameters, self.CAMADA_BUSCA, context)
        camada_ref = self.parameterAsVectorLayer(parameters, self.CAMADA_REFERENCIA, context)

        campo_municipio = self.parameterAsString(parameters, self.CAMPO_MUNICIPIO, context)
        campo_mslink = self.parameterAsString(parameters, self.CAMPO_MSLINK, context)
        campo_barramento = self.parameterAsString(parameters, self.CAMPO_BARRAMENTO, context)

        raio = self.parameterAsDouble(parameters, self.RAIO, context)
        criar_camada = self.parameterAsBool(parameters, self.CRIAR_CAMADA, context)

        # -----------------------------------------------------
        # DISTÂNCIA
        # -----------------------------------------------------

        dist_area = QgsDistanceArea()
        dist_area.setSourceCrs(camada_busca.sourceCrs(), context.transformContext())
        dist_area.setEllipsoid(QgsProject.instance().ellipsoid())

        # -----------------------------------------------------
        # TRANSFORM
        # -----------------------------------------------------

        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")

        transform = None

        if camada_busca.sourceCrs() != crs_wgs84:
            transform = QgsCoordinateTransform(
                camada_busca.sourceCrs(),
                crs_wgs84,
                context.transformContext()
            )

        # -----------------------------------------------------
        # SPATIAL INDEX
        # -----------------------------------------------------

        feedback.pushInfo("Criando Spatial Index...")

        spatial_index = QgsSpatialIndex(camada_ref.getFeatures())

        features_ref = {f.id(): f for f in camada_ref.getFeatures()}

        # -----------------------------------------------------
        # OUTPUT
        # -----------------------------------------------------

        sink = None
        sink_id = None

        if criar_camada:

            fields_saida = QgsFields()

            fields_saida.append(QgsField("municipio", QVariant.String))
            fields_saida.append(QgsField("mslink_pg", QVariant.String))
            fields_saida.append(QgsField("barramento", QVariant.String))
            fields_saida.append(QgsField("lat", QVariant.Double))
            fields_saida.append(QgsField("long", QVariant.Double))

            (sink, sink_id) = self.parameterAsSink(
                parameters,
                self.CAMADA_SAIDA,
                context,
                fields_saida,
                QgsWkbTypes.Point,
                crs_wgs84
            )

        # -----------------------------------------------------

        features = list(camada_busca.getFeatures())
        total = len(features)

        pontos_isolados = []
        pontos_saida = []

        camada_busca.removeSelection()

        for i, feature in enumerate(camada_busca.getFeatures()):

            if feedback.isCanceled():
                break

            feedback.setProgress(int(i / total * 100))

            geom = feature.geometry()

            if geom.isNull():
                continue

            ponto = self.get_point(geom)

            nearest_ids = spatial_index.nearestNeighbor(ponto, 2)

            isolado = True

            for cid in nearest_ids:

                if camada_busca.id() == camada_ref.id() and feature.id() == cid:
                    continue

                feat_cand = features_ref[cid]
                geom_cand = feat_cand.geometry()

                if geom_cand.isNull():
                    continue

                ponto_cand = self.get_point(geom_cand)

                distancia = dist_area.measureLine(ponto, ponto_cand)

                if distancia <= raio:
                    isolado = False
                    break

            if isolado:

                pontos_isolados.append(feature.id())

                if criar_camada:

                    geom_saida = QgsGeometry(geom)

                    if transform:
                        geom_saida.transform(transform)

                    pt = geom_saida.asPoint()

                    lat = pt.y()
                    long = pt.x()

                    feat_saida = QgsFeature()
                    feat_saida.setGeometry(geom_saida)

                    feat_saida.setAttributes([
                        feature[campo_municipio],
                        feature[campo_mslink],
                        feature[campo_barramento],
                        lat,
                        long
                    ])

                    pontos_saida.append(feat_saida)

        # -----------------------------------------------------

        if pontos_isolados:
            camada_busca.selectByIds(pontos_isolados)
            feedback.pushInfo(f"{len(pontos_isolados)} pontos isolados encontrados")

        if criar_camada and pontos_saida:
            sink.addFeatures(pontos_saida, QgsFeatureSink.FastInsert)

        resultado = {"Pontos_Isolados": len(pontos_isolados)}

        if criar_camada and sink_id:
            resultado[self.CAMADA_SAIDA] = sink_id

        return resultado