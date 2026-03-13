# QGIS Spatial Toolkit
 
Coleção de Processing Algorithms para QGIS desenvolvidas para
automatizar tarefas de cadastro e análise de dados geoespaciais.
 
Cada ferramenta resolve um problema específico que aparece no
dia a dia de quem trabalha com cadastro de infraestrutura urbana.
 
## Ferramentas
 
| Script | O que faz | Quando usar |
|--------|-----------|-------------|
| Mover por Proximidade | Move pontos para a estrutura mais próxima dentro de um raio | Quando não há campo de vínculo disponível |
| Mover por Referência | Move pontos usando campo-chave como vínculo | Quando há ID ou código de referência |
| Selecionar Isolados | Seleciona pontos sem vizinhos dentro de um raio | Identificar registros novos não presentes na base |
| Detector de Alvos | Gera polígonos de áreas com potencial de cadastro | Análise cruzada de múltiplas camadas |
 
## Como instalar
 
1. Abra o QGIS
2. Menu: Configurações → Editor de Scripts do Processing
3. Copie o arquivo .py desejado para a pasta de scripts
4. Recarregue os algoritmos (F5 na caixa de ferramentas)
5. Procure o script pelo nome na caixa de ferramentas Processing
 
## Requisitos
 
- QGIS 3.x
- Funciona com qualquer camada de pontos (SHP, GeoJSON, GPKG, etc.)
- Não requer instalação de dependências externas
 
## Documentação individual
 
Cada ferramenta tem documentação própria em [docs/](docs/).
 
---
 
João Vitor do Prado · linkedin.com/in/joao-do-prado · São Luís, Maranhão
