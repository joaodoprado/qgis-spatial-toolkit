from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsSpatialIndex,
    QgsGeometry,
    QgsPointXY,
    QgsDistanceArea,
    QgsWkbTypes,
    QgsFeature
)
import math


class MoveToReference(QgsProcessingAlgorithm):

    ORIGEM = "ORIGEM"
    DESTINO = "DESTINO"
    CAMPO_ORIGEM = "CAMPO_ORIGEM"
    CAMPO_DESTINO = "CAMPO_DESTINO"
    DIST_MIN = "DIST_MIN"
    MOVER_DIRETO = "MOVER_DIRETO"
    OUTPUT = "OUTPUT"

    def name(self):
        return "move_features_to_reference"

    def displayName(self):
        return "Mover Feições para Referência"

    def group(self):
        return "Spatial Tools"

    def groupId(self):
        return "spatial_tools"

    def createInstance(self):
        return MoveToReference()

    # -----------------------------------------------------

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterFeatureSource(self.ORIGEM, "De onde mover"))
        self.addParameter(QgsProcessingParameterFeatureSource(self.DESTINO, "Para onde mover"))

        self.addParameter(QgsProcessingParameterField(
            self.CAMPO_ORIGEM, "Campo chave origem",
            parentLayerParameterName=self.ORIGEM
        ))
        self.addParameter(QgsProcessingParameterField(
            self.CAMPO_DESTINO, "Campo chave destino",
            parentLayerParameterName=self.DESTINO
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.DIST_MIN, "Distância mínima (metros)", defaultValue=0.5
        ))

        self.addParameter(QgsProcessingParameterBoolean(
            self.MOVER_DIRETO, "Mover diretamente na camada origem", defaultValue=False
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, "Resultado (caso não mova direto)", optional=True
        ))

    # -----------------------------------------------------
    # HELPERS
    # -----------------------------------------------------

    def limpar_chave(self, valor):
        if valor is None:
            return None
        s = str(valor).strip().upper()
        if s.startswith("GLUX"):
            s = s[4:]
        elif s.startswith("GL"):
            s = s[2:]
        s = s.lstrip("0")
        return s if s else None

    def veio_de_newfromfield(self, valor):
        if valor is None:
            return False
        return "NEWFROMFIELD" in str(valor).upper()

    def dist_euclidiana(self, p1, p2):
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return math.sqrt(dx * dx + dy * dy)

    def extrair_pt(self, geom):
        """Extrai QgsPointXY com floats Python puros — sem referência C++."""
        if geom.isNull():
            return None
        raw = geom.asMultiPoint()[0] if geom.isMultipart() else geom.asPoint()
        return QgsPointXY(float(raw.x()), float(raw.y()))

    # -----------------------------------------------------

    def processAlgorithm(self, parameters, context, feedback):

        origem = self.parameterAsSource(parameters, self.ORIGEM, context)
        destino = self.parameterAsSource(parameters, self.DESTINO, context)

        campo_origem  = self.parameterAsString(parameters, self.CAMPO_ORIGEM, context)
        campo_destino = self.parameterAsString(parameters, self.CAMPO_DESTINO, context)
        dist_min      = self.parameterAsDouble(parameters, self.DIST_MIN, context)
        mover_direto  = self.parameterAsBool(parameters, self.MOVER_DIRETO, context)

        dist_calc = QgsDistanceArea()
        dist_calc.setSourceCrs(origem.sourceCrs(), context.transformContext())
        dist_calc.setEllipsoid('WGS84')

        # -------------------------------------------------
        # CARGA DO DESTINO — tipos Python puros, sem QgsFeature
        # -------------------------------------------------

        feedback.pushInfo("Carregando destino...")

        index         = QgsSpatialIndex()
        destino_pontos = {}   # fid (int) → QgsPointXY
        fid_chave      = {}   # fid (int) → chave (str)
        chave_dict     = {}   # chave (str) → [fid, ...]

        for f in destino.getFeatures():
            fid  = f.id()
            pt   = self.extrair_pt(f.geometry())
            if pt is None:
                continue
            destino_pontos[fid] = pt
            index.addFeature(f)
            chave = self.limpar_chave(f[campo_destino])
            if chave:
                fid_chave[fid] = chave
                chave_dict.setdefault(chave, []).append(fid)

        feedback.pushInfo(f"Destino: {len(destino_pontos)} pts, {len(chave_dict)} chaves.")

        # -------------------------------------------------
        # OUTPUT (sink)
        # -------------------------------------------------

        sink = None
        sink_id = None
        if not mover_direto:
            (sink, sink_id) = self.parameterAsSink(
                parameters, self.OUTPUT, context,
                origem.fields(), QgsWkbTypes.Point, origem.sourceCrs()
            )

        # -------------------------------------------------
        # CONTADORES
        # -------------------------------------------------

        movidos          = 0
        ignorados        = 0
        ja_no_poste      = 0
        ignorados_newfrom = 0
        total            = origem.featureCount()

        # -------------------------------------------------
        # FASE 1 — LEITURA: calcula movimentos, nada é editado
        #
        # Armazena tudo como tipos Python puros:
        #   edicoes_pendentes : { fid_orig(int) → QgsPointXY }
        #   sink_rows         : [ (dict_atributos, QgsPointXY) ]
        # -------------------------------------------------

        edicoes_pendentes = {}
        sink_rows = []

        fields = origem.fields()
        field_names = [fields.at(i).name() for i in range(fields.count())]

        for i, f in enumerate(origem.getFeatures()):

            if feedback.isCanceled():
                break

            feedback.setProgress(int(i / total * 100))

            fid_orig = f.id()
            barr     = f[campo_origem]
            pt_orig  = self.extrair_pt(f.geometry())

            # Captura atributos como dict Python puro agora,
            # enquanto a feature ainda está viva no iterator
            attrs = {n: f[n] for n in field_names}

            def enqueue_original():
                if not mover_direto and sink is not None:
                    sink_rows.append((attrs, pt_orig))

            if self.veio_de_newfromfield(barr):
                ignorados_newfrom += 1
                enqueue_original()
                continue

            chave = self.limpar_chave(barr)

            if chave is None or pt_orig is None:
                ignorados += 1
                enqueue_original()
                continue

            candidatos = chave_dict.get(chave)
            if not candidatos:
                ignorados += 1
                enqueue_original()
                continue

            # Busca do mais próximo por euclidiana
            menor_eucl = None
            melhor_pt  = None

            if len(candidatos) <= 5:
                for fid_d in candidatos:
                    pt_ref = destino_pontos[fid_d]
                    d = self.dist_euclidiana(pt_orig, pt_ref)
                    if menor_eucl is None or d < menor_eucl:
                        menor_eucl = d
                        melhor_pt  = pt_ref
            else:
                for n_viz in (5, 20):
                    for nid in index.nearestNeighbor(pt_orig, n_viz):
                        if fid_chave.get(nid) != chave:
                            continue
                        pt_ref = destino_pontos[nid]
                        d = self.dist_euclidiana(pt_orig, pt_ref)
                        if menor_eucl is None or d < menor_eucl:
                            menor_eucl = d
                            melhor_pt  = pt_ref
                    if melhor_pt is not None:
                        break

            if melhor_pt is None:
                ignorados += 1
                enqueue_original()
                continue

            # Distância elipsoidal só no vencedor
            dist_real = dist_calc.measureLine(pt_orig, melhor_pt)

            if dist_real < dist_min:
                ja_no_poste += 1
                enqueue_original()
                continue

            # Acumula — sem editar nada ainda
            if mover_direto:
                edicoes_pendentes[fid_orig] = melhor_pt
            else:
                sink_rows.append((attrs, melhor_pt))

            movidos += 1

        # -------------------------------------------------
        # FASE 2A — EDIÇÃO DIRETA (iterator já encerrado)
        #
        # FIX: usar dataProvider().changeGeometryValues()
        # em vez de layer.changeGeometry() individualmente.
        #
        # changeGeometry() dispara QUndoStack por chamada,
        # que atualiza QUndoView na UI e causa access violation
        # quando a view tem estado inconsistente (bug QGIS Windows).
        #
        # changeGeometryValues() faz uma única operação em batch
        # no provider, sem disparar o undo stack por feature.
        # -------------------------------------------------

        if mover_direto and edicoes_pendentes:

            feedback.pushInfo(f"Aplicando {len(edicoes_pendentes)} edições via dataProvider...")

            layer_id = parameters[self.ORIGEM]
            layer    = context.project().mapLayer(layer_id)

            if layer is None:
                feedback.reportError("Camada origem não encontrada no projeto.")
            else:
                # Bloqueia sinais Qt durante a edição para evitar
                # que QUndoView e QItemSelectionModel acessem
                # estado inválido enquanto o provider atualiza
                layer.blockSignals(True)
                try:
                    was_editable = layer.isEditable()
                    if not was_editable:
                        layer.startEditing()

                    # Batch update: { fid → QgsGeometry } — uma única chamada
                    geom_map = {
                        fid: QgsGeometry.fromPointXY(pt)
                        for fid, pt in edicoes_pendentes.items()
                    }
                    layer.dataProvider().changeGeometryValues(geom_map)
                    layer.triggerRepaint()

                    feedback.pushInfo("Edições aplicadas. Salve a camada para persistir.")
                finally:
                    layer.blockSignals(False)

        # -------------------------------------------------
        # FASE 2B — ESCRITA NO SINK
        # -------------------------------------------------

        elif not mover_direto and sink is not None:

            feedback.pushInfo(f"Escrevendo {len(sink_rows)} feições no sink...")

            for attrs, pt in sink_rows:
                nova_f = QgsFeature(fields)
                for nome, val in attrs.items():
                    nova_f[nome] = val
                if pt is not None:
                    nova_f.setGeometry(QgsGeometry.fromPointXY(pt))
                sink.addFeature(nova_f)

        # -------------------------------------------------
        # RESULTADO
        # -------------------------------------------------

        feedback.pushInfo("============== RESULTADO ==============")
        feedback.pushInfo(f"Movidos:              {movidos}")
        feedback.pushInfo(f"Ignorados:            {ignorados}")
        feedback.pushInfo(f"Já no poste:          {ja_no_poste}")
        feedback.pushInfo(f"Ignorados NEWFROMFIELD: {ignorados_newfrom}")
        feedback.pushInfo("=======================================")

        if mover_direto:
            return {}

        return {self.OUTPUT: sink_id}