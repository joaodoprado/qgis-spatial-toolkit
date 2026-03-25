# QGIS Spatial Toolkit

Ferramentas para automação de problemas reais de cadastro de infraestrutura urbana no QGIS.

Este projeto foi desenvolvido com base em desafios enfrentados no dia a dia, como inconsistência de coordenadas, ausência de vínculos entre dados e identificação de áreas não cadastradas.

As ferramentas reduzem trabalho manual, aumentam a confiabilidade dos dados e aceleram o processo de análise espacial.

## Impacto Real

As ferramentas deste projeto foram aplicadas em ambiente profissional, gerando:

- Redução de tempo de execução de análises de ~20h para ~2h
- Ganho médio de produtividade de aproximadamente 90%
- Automação de processos de fiscalização e validação de dados geoespaciais
- Aplicação em múltiplos municípios

## Ferramentas

| Script | O que faz | Quando usar |
|--------|-----------|-------------|
| [Mover por Proximidade](/docs/01_mover_por_proximidade.md) | Move pontos para a estrutura mais próxima dentro de um raio | Quando não há campo de vínculo disponível |
| [Mover por Referência](/docs/02_mover_por_referencia.md) | Move pontos usando campo-chave como vínculo | Quando há ID ou código de referência |
| [Selecionar Isolados](/docs/03_selecionar_isolados.md) | Seleciona pontos sem vizinhos dentro de um raio | Identificar registros novos não presentes na base |
| [Detector de Alvos](/docs/04_detector_de_alvos.md) | Gera polígonos de áreas com potencial de cadastro | Análise cruzada de múltiplas camadas |

## Exemplos visuais

### Detector de Alvos
Polígonos de áreas com potencial de cadastro gerados a partir do cruzamento entre postes, rede BT e IP existente.

![Detector de Alvos - resultado](/prints/detectar_02.png)

### Mover por Referência
Pontos deslocados (laranja) sendo corrigidos para a posição de referência (branco) usando campo-chave como vínculo.

![Mover por Referência - antes e depois](/prints/mover_feições_por_referencia_01.png)

### Selecionar Isolados
Identificação de pontos sem vizinhos na base de referência dentro do raio configurado.

![Selecionar Isolados](/prints/isolados_01.png)

## Como instalar

1. Abra o QGIS
2. Menu: Configurações → Editor de Scripts do Processing
3. Copie o arquivo `.py` desejado para a pasta de scripts
4. Recarregue os algoritmos (F5 na caixa de ferramentas)
5. Procure o script pelo nome na caixa de ferramentas Processing

## Requisitos

- QGIS 3.x
- Funciona com qualquer camada de pontos (SHP, GeoJSON, GPKG, etc.)
- Não requer instalação de dependências externas

## Dados de exemplo

A pasta [`exemplos/`](exemplos/) contém camadas GeoJSON sintéticas
para testar cada ferramenta sem precisar de dados reais.

## Documentação individual

Cada ferramenta tem documentação própria em [`docs/`](docs/).

---

João Vitor do Prado · [linkedin.com/in/joao-do-prado](https://www.linkedin.com/in/joao-do-prado/) · São Luís, Maranhão
