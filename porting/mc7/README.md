# PanVK ARM64 para Mali-G720 MC7 (MT6899)

A cópia parte de `panvk-g720-botw-vertex-compat@8ae1246d88bab3dc721dcabd013c4b700ebb5542`, que já integra Mesa 26.3.0-devel, Kbase e CSF. O registro de BOTWRecomp cita o pacote `c5d20d2` e registra o driver Vulkan do sistema, ID 9. O commit `c5d20d249fc2805b06466b52de3725678e9da417` forneceu o ajuste de tamanho inicial do heap de tiler.

| Área | Integração e verificação |
| --- | --- |
| Optimized | Corrigido o endereço de 64 bits do helper de provoking vertex (branch `panvk/g720-mc7-fnaddr-fix`). A regra linear de AHB/ANB de `port/faux123-1.1.9-g720-mc7` foi adaptada à API WSI da cópia. O uso do número de registradores reportado pelo CSF já estava integrado. |
| Placed Memory Maps | O backend toma a decisão com base na alocação, importação, alias no endereço escolhido e verificação bidirecional com `mprotect`. A correção 091 usa BO compartilhável para memória host-visible quando a feature está habilitada. A adaptação do overlay 096 distingue SAME_VA de NEED_MMAP. |
| Heap Renew | Intervalo 256 e limiar de trabalho 131072, com as opções de ambiente existentes. O tamanho inicial é de até quatro chunks por padrão. |
| NIR | O intrinsic `load_geometry_param_buffer_poly` já constava na classificação conservadora de divergência. |
| Texturas BC | Mantida a detecção de formatos nativos. Os patches 022, 039, 040, 108 e 150 da série reconciliada apresentaram conflito de contexto nesta revisão. A branch `g720-mc7-bc-emul` também registra a retirada da aplicação automática dessa série. |
| Fusion Patch | Nenhum patch ou commit com esse identificador foi localizado nos insumos examinados. |

Faux123 v1.1.9 é a referência do port. O código privado do release oficial, incluindo 49 patches, ficou fora do material disponível. A validação no aparelho ainda precisa cobrir inicialização do Vulkan, alias no MT6899, apresentação WSI, amostragem BC e cenas do BOTWRecomp.

Com NDK r27 apontado por `ANDROID_NDK_HOME` e dependências declaradas no workflow, execute `bash setup.sh` e `python3 porting/mc7/package.py`. O pacote exige ELF64 AArch64 para Android API 31, símbolo HAL `HMI` e metadados na raiz do ZIP.
