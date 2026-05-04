Análisis Sistémico de la Detección Temprana del Cáncer: Fallas Estructurales en la Atención Primaria, la Infrautilización de Datos No Estructurados y la Transformación Mediante Arquitecturas de Inteligencia Artificial
El sistema de salud global se encuentra en una encrucijada crítica donde la efectividad del tratamiento oncológico está severamente limitada no por la falta de terapias avanzadas, sino por la incapacidad sistémica de identificar la enfermedad en sus estadios más precoces. La transición de un modelo de "atención al enfermo" reactivo hacia un paradigma de cuidado proactivo y predictivo es la necesidad más urgente de la medicina contemporánea.[1] En este contexto, la atención primaria actúa como el primer y más vital filtro, donde la interacción entre el paciente y el médico general puede determinar la diferencia entre una intervención curativa y un manejo paliativo. Sin embargo, este primer punto de contacto está plagado de cuellos de botella que oscilan desde sesgos cognitivos y presiones asistenciales hasta una infraestructura de datos que ignora sistemáticamente la mayor parte de la información clínica relevante.[2, 3] El presente informe analiza exhaustivamente las fallas en el triaje y la detección temprana, evaluando el impacto de la información no estructurada y proponiendo un marco de intervención basado en agentes de inteligencia artificial para rediseñar los flujos de trabajo oncológicos.
El Agujero Negro del Diagnóstico: Factores de Retraso en la Atención Primaria
La fase inicial del diagnóstico oncológico a menudo se describe como un "agujero negro" debido a la confluencia de variables que oscurecen la presencia de la enfermedad. El retraso diagnóstico se manifiesta en tres niveles interconectados: el paciente, el médico de atención primaria y el sistema de salud en su conjunto.[4, 5] La complejidad radica en que el cáncer, en sus etapas iniciales, rara vez se presenta con los "signos de alarma" clásicos descritos en los libros de texto; en cambio, se manifiesta a través de una constelación de síntomas vagos, heterogéneos y compartidos con patologías benignas de alta prevalencia.[4, 6]
La Psicología de la Evaluación de Síntomas por el Paciente
El retraso a menudo comienza antes de la primera consulta médica. La interpretación que el paciente hace de sus propios síntomas es un proceso dinámico y a menudo sesgado. Se han identificado cuatro patrones principales de interpretación de síntomas que afectan la búsqueda de ayuda: la percepción de síntomas como compatibles con un estado normal de salud, problemas vinculados a eventos específicos (como estrés o lesiones menores), enfermedades leves o crónicas preexistentes, y un estado general de malestar no específico.[6, 7]
Los pacientes tienden a "normalizar" cambios sutiles en su salud. Por ejemplo, la fatiga persistente se atribuye frecuentemente al estrés laboral o a la falta de sueño, mientras que los cambios en el ritmo evacuatorio se asocian a la dieta o al envejecimiento.[7, 8] Este proceso de normalización es especialmente peligroso en cánceres como el de ovario o páncreas, donde los síntomas "susurran" antes de gritar.[9, 10] Además, barreras como el miedo al diagnóstico, la preocupación por la carga que representa para la familia y las dificultades logísticas para concertar citas contribuyen a que el paciente demore semanas o meses en buscar una evaluación profesional.[4, 5]
Desafíos Cognitivos y el Papel de la Intuición Clínica
Para el médico de atención primaria, el desafío es estadístico y cognitivo. Un médico general ve a miles de pacientes al año, pero solo una fracción mínima presentará un nuevo diagnóstico de cáncer. Dado que más del 80% de los pacientes oncológicos consultan inicialmente por síntomas inespecíficos, el umbral de sospecha debe equilibrarse con el riesgo de sobre-investigación y la saturación del sistema.[4]
La continuidad de la atención es el factor protector más importante en este nivel. La relación longitudinal permite al médico desarrollar un "sentido clínico" o "gut feeling", una combinación de señales verbales y no verbales que alertan sobre cambios sutiles en el paciente.[2] No obstante, la fragmentación actual del sistema, caracterizada por el uso extensivo de médicos suplentes (locums) y sistemas de listas abiertas donde el paciente es atendido por cualquier facultativo disponible, erosiona esta capacidad diagnóstica.[2, 6] Cuando no existe un conocimiento previo del paciente, el médico tiende a tratar el síntoma de forma aislada, perdiendo la visión de conjunto necesaria para detectar patrones de enfermedad maligna.
Presión Asistencial y el Error de Triaje
La limitación de tiempo en las consultas de atención primaria es un factor sistémico que impacta directamente en la seguridad del paciente. Las consultas breves impiden una toma de historia clínica exhaustiva y una exploración física completa, elementos cruciales para detectar masas sutiles o ganglios linfáticos inflamados.[5] Bajo presión, los médicos pueden caer en el error de cierre prematuro, atribuyendo los síntomas a una causa benigna conocida sin considerar diagnósticos diferenciales más graves.[5]
Clasificación de Problemas en el Diagnóstico de Cáncer
Puntaje de Prioridad
Categoría de Factor
Falta de conciencia pública sobre síntomas sutiles
82.5
Paciente
Pobre continuidad de la atención (fragmentación)
79.0
Sistema
Incumplimiento de guías de derivación rápida
79.0
Sistema
Tiempo insuficiente en la consulta para historial completo
78.0
Sistema
Pacientes sin médico de cabecera asignado
78.0
Paciente
Confusión de síntomas por co-morbosidades preexistentes
68.5
Cognitivo
Omisión de síntomas de alarma específicos (ej. sangrado rectal)
68.0
Cognitivo
Tabla 1: Jerarquización de barreras críticas en la detección temprana según la perspectiva de clínicos expertos.[5]
El Problema de los Datos: La Información No Estructurada en el Registro Clínico
En la era del Big Data, el sistema de salud paradójicamente padece de una ceguera informativa significativa. La mayoría de los sistemas de Registro Electrónico de Salud (EHR) están diseñados para fines administrativos y de facturación, priorizando campos estructurados como códigos de diagnóstico (ICD-10) y procedimientos. Sin embargo, la esencia de la sospecha oncológica reside en la narrativa clínica, la cual permanece oculta a los algoritmos convencionales.
La Regla del 80%: El Valor del Texto Libre
Se estima que aproximadamente el 80% de los datos de salud generados son no estructurados.[3, 11, 12] Esto incluye notas de evolución médica, transcripciones de dictados, informes de patología, hallazgos radiológicos y descripciones de la historia familiar. En el ámbito específico de la oncología y los ensayos clínicos, entre el 45% y el 70% de las variables críticas para determinar la elegibilidad, el estadio de la enfermedad y la respuesta al tratamiento residen exclusivamente en estos formatos narrativos.[3]
La información no estructurada captura matices que los menús desplegables ignoran. Por ejemplo, la descripción cualitativa del dolor, la progresión de la fatiga o la percepción del médico sobre el "aspecto" del paciente son indicadores tempranos potentes. Los estudios demuestran que integrar datos no estructurados en modelos predictivos mejora drásticamente la precisión en la identificación de riesgos clínicos, logrando áreas bajo la curva (AUROC) de hasta 0.88 en predicciones de mortalidad y resultados adversos.[11] Sin el procesamiento de estos datos, el sistema ignora pistas críticas que el médico registra pero que nadie —ni humano ni máquina— analiza de manera agregada.
Discrepancias en el Historial Familiar y la Estratificación de Riesgo
El historial de salud familiar es otra área donde la estructura de datos falla. A pesar de ser una herramienta de bajo costo para identificar individuos con alto riesgo genético (como síndromes de Lynch o HBOC), su documentación en el EHR es crónicamente deficiente.[13, 14] Existe una brecha significativa entre lo que los pacientes informan en cuestionarios especializados y lo que efectivamente se registra en su expediente médico electrónico. En muchos casos, antecedentes de cáncer de primer grado mencionados por el paciente están ausentes en las secciones correspondientes del EHR, lo que impide que el médico inicie protocolos de tamizaje temprano o derivaciones a asesoramiento genético.[14]
La falta de una "única fuente de verdad" para el historial familiar conduce a que pacientes de alto riesgo sean tratados como de riesgo promedio, perdiendo años vitales de vigilancia intensiva. La evidencia indica que el simple hecho de registrar formalmente un historial familiar —incluso si es negativo— aumenta la probabilidad de que el paciente se mantenga al día con sus pruebas de tamizaje, sugiriendo un efecto de refuerzo en la conciencia tanto del médico como del paciente.[15]
Tipos de Cáncer Vulnerables: El Desafío de la Sutileza Clínica
Basado en la evidencia recolectada, existen tipos específicos de cáncer donde el sistema de triaje falla sistemáticamente debido a la naturaleza de sus síntomas. Estos cánceres comparten una característica común: su detección temprana cambia radicalmente el pronóstico, pero sus señales iniciales son indistinguibles de dolencias comunes de la vida diaria.
Cáncer de Páncreas y el Problema de la Ubicación Anatómica
El cáncer de páncreas es quizás el desafío más formidable para la detección temprana. Debido a que el órgano se encuentra profundamente en el abdomen, los tumores pequeños no son palpables y rara vez causan síntomas obstructivos tempranos.[9, 10] Cuando aparecen síntomas como la pérdida de peso inexplicable, el dolor de espalda o la indigestión vaga, la enfermedad a menudo ya ha invadido estructuras vasculares críticas o se ha metastatizado.[16, 17]
La precisión en la etapificación inicial es extremadamente baja en el cáncer de páncreas; estudios sugieren que hasta el 80% de los pacientes considerados inicialmente en etapa 1 o 2 son re-etapificados a niveles más avanzados tras la cirugía.[17] Esto subraya la necesidad de herramientas de diagnóstico mucho más sensibles y precoces que las actuales.
Cáncer de Ovario: Los Síntomas que "Susurran"
El cáncer de ovario es frecuentemente diagnosticado en etapas III o IV, cuando las tasas de supervivencia caen drásticamente. Sus síntomas —hinchazón abdominal, saciedad temprana, presión pélvica y urgencia urinaria— son tan comunes en la población femenina que a menudo son ignorados por las pacientes o atribuidos a problemas gastrointestinales o al envejecimiento por parte de los médicos.[10, 18] Sin embargo, la diferencia en la supervivencia a 5 años según el estadio al diagnóstico es una de las más pronunciadas en oncología, lo que justifica cualquier esfuerzo tecnológico por adelantar el diagnóstico.
Tipo de Cáncer
Supervivencia 5 Años (Etapa 1/Localizado)
Supervivencia 5 Años (Etapa 4/Distante)
Síntomas Precursores Críticos
Ovario
92.6% - 95.0%
15.0% - 30.2%
Hinchazón, saciedad rápida, dolor pélvico
Páncreas
37.0% - 83.0%
3.0%
Indigestión, pérdida de peso, dolor abdominal vago
Pulmón
59.0%
6.0%
Tos persistente, ronquera, fatiga
Colorrectal
~90.0%
~14.0%
Sangre en heces, anemia, cambios en ritmo
Tabla 2: Comparativa de tasas de supervivencia y el impacto crítico del diagnóstico temprano frente al avanzado.[9, 17, 19, 20, 21, 22]
Cáncer de Pulmón y Malignidades Hematológicas
En el cáncer de pulmón, la confusión con infecciones respiratorias recurrentes o bronquitis crónica en fumadores retrasa la realización de radiografías de tórax cruciales.[10, 19] Por otro lado, los cánceres de sangre como el linfoma se presentan con síntomas constitucionales (fiebre, sudores nocturnos, fatiga) que el paciente a menudo minimiza y el médico confunde con procesos virales comunes hasta que la enfermedad es sistémica.[6, 19]
Fallas en el Flujo Actual (Workflows): Anatomía de una Desconexión
El recorrido del paciente desde el síntoma difuso hasta el tratamiento oncológico puede visualizarse como una cadena de custodia de información y decisiones que se rompe con facilidad. El flujo actual no es un proceso lineal fluido, sino una serie de saltos entre niveles asistenciales con poca retroalimentación.
Paso 1: Aparición del Síntoma y Appraisal del Paciente
El proceso se inicia en el entorno doméstico. El paciente monitoriza sus síntomas de forma periódica. El punto de falla ocurre cuando el paciente decide que el síntoma es "normal" o "atribuible a un evento". La falta de educación pública y el miedo actúan como bloqueadores de la primera consulta.[4, 7] En esta etapa, el sistema de salud es pasivo; espera a que el paciente tome la iniciativa.
Paso 2: La Consulta Inicial en Atención Primaria
El paciente presenta su síntoma al médico de AP. Aquí, el flujo se ralentiza por la falta de tiempo (promedio de 10 minutos por consulta). El médico debe decidir entre: a) Observar (safety netting), b) Investigar (pruebas básicas), o c) Derivar.[2, 23]
Punto de Ruptura: Si el médico no tiene acceso a un historial longitudinal claro o si el paciente ve a un médico diferente al habitual, la sospecha no se consolida. La falta de protocolos de entrega entre facultativos (handover) hace que cada consulta se trate como un evento aislado.
Paso 3: El Protocolo de Red de Seguridad (Safety Netting)
El safety netting es la práctica de dar instrucciones claras sobre qué hacer si el síntoma no mejora. Neighbour lo definió con tres preguntas: "¿Si tengo razón, qué espero que pase? ¿Cómo sabré si me equivoco? ¿Qué haré entonces?".[24]
Punto de Ruptura: El safety netting es a menudo verbal y vago. Los pacientes no retienen la información o no comprenden la importancia de volver si el síntoma persiste. Además, no suele haber un sistema electrónico que alerte al médico si el paciente no regresó tras un tiempo determinado.[25, 26]
Paso 4: Pruebas Diagnósticas en Comunidad
El médico de AP solicita análisis de sangre o imágenes básicas.
Punto de Ruptura: El fenómeno del "falso negativo" o el resultado "normal". Muchos cánceres en etapa temprana no alteran los marcadores sanguíneos estándar. Un resultado normal a menudo tranquiliza falsamente al médico y al paciente, deteniendo la investigación a pesar de que el síntoma original persiste (el llamado "pitfall de los resultados normales").[26]
Paso 5: La Derivación al Especialista (The Referral Gap)
Se inicia la derivación a atención secundaria.
Punto de Ruptura: La burocracia hospitalaria y la mala calidad de la información en la solicitud de derivación. Las solicitudes a menudo carecen de la "pregunta clínica" central o no adjuntan los resultados de pruebas previas.[27, 28] Esto genera que la administración del hospital retrase la cita o que el especialista tenga que repetir pruebas innecesarias, consumiendo tiempo valioso donde el tumor sigue creciendo.
Paso 6: Triaje en Atención Secundaria y Diagnóstico Final
El paciente es visto en el hospital, se realiza la biopsia y se confirma el diagnóstico.
Punto de Ruptura: El retraso entre la derivación y la primera cita con el oncólogo puede ser de semanas. En cánceres de progresión rápida, este intervalo puede significar el paso de una enfermedad resecable a una irresecable.[4, 16]
Oportunidad para Agentes de IA: Hacia un Triaje Aumentado y Proactivo
La arquitectura de soluciones de IA para la oncología en atención primaria no debe verse como un reemplazo del juicio médico, sino como una capa de inteligencia ambiental que elimina la fricción y la invisibilidad de los datos. Un sistema de agentes de IA basado en Procesamiento de Lenguaje Natural (NLP) avanzado y modelos de lenguaje de gran escala (LLM) puede intervenir específicamente en los puntos de falla identificados en el workflow.
Extracción de Señales en Tiempo Real desde el Texto Libre
La primera oportunidad reside en la transformación de las notas de evolución médica en datos estructurados accionables. Mediante técnicas de Reconocimiento de Entidades Nombradas (NER) y extracción de relaciones, un agente de IA puede analizar cada nueva nota introducida por el médico general en el EHR.[29, 30]
Intervención: El agente puede detectar patrones de síntomas sutiles que se han repetido en las últimas tres consultas, incluso si fueron atendidas por médicos diferentes. Al identificar una "trayectoria de síntomas" sospechosa (ej. fatiga + cambio en hábito urinario + dolor de espalda leve en una mujer de 60 años), el agente puede elevar una alerta de riesgo de cáncer de ovario o páncreas directamente en el punto de atención.[31, 32]
Automatización y Dinamización de la Red de Seguridad (Safety Netting Digital)
El safety netting actual falla por ser pasivo y dependiente de la memoria. Un agente de IA puede convertir esto en un proceso activo y automatizado.
Intervención: Al final de la consulta, el agente detecta que el médico ha optado por un enfoque de "observar y esperar". El sistema genera automáticamente una tarea de seguimiento en el EHR y envía instrucciones personalizadas al paciente vía SMS o portal de salud. Si el paciente no reporta mejoría o no agenda una cita de seguimiento en el plazo previsto (ej. 2 semanas), el agente notifica proactivamente al equipo de enfermería o al médico para un contacto proactivo.[23, 26]
Optimización de la Calidad de la Derivación (Referral Quality Agent)
Para cerrar la brecha de comunicación entre niveles asistenciales, los agentes de IA pueden actuar como mediadores de información.
Intervención: Cuando un médico decide derivar a un paciente, el agente de IA puede "pre-redactar" la solicitud de derivación, extrayendo automáticamente del historial clínico todos los datos relevantes: síntomas específicos, resultados de laboratorio recientes, imágenes previas y factores de riesgo familiar.[30, 33] Esto asegura que el especialista reciba un resumen clínico de alta calidad y que la derivación sea categorizada correctamente por urgencia, evitando que el paciente se pierda en la burocracia hospitalaria.[28, 34]
El Copiloto del Historial Familiar y Riesgo Genético
Dado que los médicos a menudo carecen de tiempo o conocimiento para mapear pedigríes complejos, un agente de IA puede asumir esta carga.
Intervención: Antes de la consulta, un agente conversacional (chatbot clínico) puede interactuar con el paciente para recopilar y verificar su historial familiar de forma exhaustiva.[13, 14] El agente aplica algoritmos de validación de riesgo (como los criterios de HBOC o Lynch) y presenta al médico un resumen de riesgo junto con recomendaciones de tamizaje específicas basadas en guías clínicas actualizadas.[16, 35]
Triaje Acelerado de Resultados de Patología y Radiología
El tiempo que transcurre desde que se realiza una prueba hasta que el médico la revisa es un cuello de botella crítico.
Intervención: Un agente de NLP puede monitorizar continuamente el flujo de entrada de informes de patología y radiología. Utilizando modelos entrenados específicamente para oncología (como CAN-TRI-NLP), el sistema puede identificar hallazgos malignos o de alto riesgo con una precisión del 98-100% y alertar instantáneamente al oncólogo y al médico de AP, incluso antes de que el informe sea revisado manualmente, permitiendo el inicio inmediato del tratamiento neoadyuvante o la cirugía.[36]
La implementación de estos agentes de IA no solo reduciría la carga cognitiva del médico, sino que actuaría como una verdadera "red de seguridad" tecnológica, asegurando que ningún paciente sea ignorado por el sistema debido a la sutileza de su condición o a la fragmentación de su cuidado. En un entorno donde cada día de adelanto en el diagnóstico cuenta, la IA se posiciona como el aliado indispensable para cerrar el agujero negro del diagnóstico oncológico.
--------------------------------------------------------------------------------
AI in medical diagnostics: Early detection and prevention, https://diagnostics.roche.com/global/en/healthcare-transformers/article/ai-preventive-healthcare.html
Primary care delays in diagnosing cancer: what is causing them and ..., https://pmc.ncbi.nlm.nih.gov/articles/PMC3807772/
Unlocking Unstructured Health Data: Scaling eSource-Enabled ..., https://www.appliedclinicaltrialsonline.com/view/unlocking-unstructured-health-data-scaling-esource-enabled-clinical-trials
Delay in Cancer Diagnosis: Causes and Possible Solutions - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC4996960/
Preventing delayed diagnosis of cancer: clinicians' views on main ..., https://pmc.ncbi.nlm.nih.gov/articles/PMC5140077/
What causes delays in diagnosing blood cancers? A rapid review of the evidence, https://openresearch.surrey.ac.uk/esploro/outputs/journalArticle/What-causes-delays-in-diagnosing-blood/99757965702346
What causes delays in diagnosing blood cancers? A rapid review of the evidence | Primary Health Care Research & Development, https://www.cambridge.org/core/journals/primary-health-care-research-and-development/article/what-causes-delays-in-diagnosing-blood-cancers-a-rapid-review-of-the-evidence/0DA1FD297A02957BD3DF019AF2BA0E2A
Subtle Cancer Symptoms You Might Overlook - Banner Health, https://www.bannerhealth.com/healthcareblog/teach-me/subtle-cancer-symptoms-you-might-overlook
Hardest Cancers to Diagnose Early: Powerful Challenges Reviewed - Liv Hospital, https://int.livhospital.com/hardest-cancers-to-diagnose-early-powerful/
These 5 Cancers are Difficult to Detect | Moffitt, https://www.moffitt.org/taking-care-of-your-health/taking-care-of-your-health-story-archive/these-5-cancers-are-difficult-to-detect/
Integrating Structured and Unstructured EHR Data for Predicting Mortality by Machine Learning and Latent Dirichlet Allocation Method - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC10001457/
How Unstructured Healthcare Data & NLP Reveal Missed Diagnoses - Amplity, https://amplity.com/news/how-unstructured-medical-data-nlp-reveal-missed-diagnoses
Family Health History and Cancer - CDC, https://www.cdc.gov/cancer/risk-factors/family-health-history.html
Comparison of a Focused Family Cancer History Questionnaire to Family History Documentation in the Electronic Medical Record - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC8796064/
Association Between Documented Family History of Cancer and Screening for Breast and Colorectal Cancer - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC4041693/
Pancreatic Cancer: Symptoms, Causes & Treatment - Cleveland Clinic, https://my.clevelandclinic.org/health/diseases/15806-pancreatic-cancer
Pancreatic Cancer: Study Finds Most Early Staging Inaccurate - Cedars-Sinai, https://www.cedars-sinai.org/newsroom/pancreatic-cancer-study-finds-most-early-staging-inaccurate/
6 Silent cancers that you need to keep an eye on | HCG, https://www.hcgoncology.com/blog/6-silent-cancers-that-you-need-to-keep-an-eye-on/
Common Cancers Doctors Fail To Diagnose Early | Powers & Santola, LLP, https://powers-santola.com/blog/common-cancers-doctors-fail-to-diagnose-early/
Survival for ovarian cancer, https://www.cancerresearchuk.org/about-cancer/ovarian-cancer/survival
Ovarian Cancer Remains Deadly, Rates Declining Slowly, https://www.jhoponline.com/web-exclusives/ovarian-cancer-remains-deadly-rates-declining-slowly
Cancer Stat Facts: Ovarian Cancer - SEER, https://seer.cancer.gov/statfacts/html/ovary.html
Safety netting for cancer diagnosis in primary care - GM PCB, https://gmpcb.org.uk/general-practice/gp-excellence/resources/safety-netting-cancer-diagnosis-primary-care/
Safety netting for primary care: evidence from a literature review - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC6301356/
How does safety netting for lung cancer symptoms help patients to reconsult appropriately? A qualitative study - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC9298706/
Cancer Safety Netting: Top 10 Tips for Primary Care, https://www.macmillan.org.uk/healthcare-professionals/for-your-role/doctor/gp/top-tips-for-primary-care/cancer-safety-netting-tips
Primary Care Checklist Suggestions for Assessing Referral Process, https://www.medchi.org/Portals/18/Files/Practice%20Services/primary-care-checklist-for-referral-process-assessment-and-critical-elements%20(1).pdf?ver=2023-08-18-114031-763
Managing Referrals – Providing a Patient-Centered Referral Experience - CMS, https://www.cms.gov/priorities/innovation/files/x/tcpi-changepkgmod-referrals.pdf
Extracting cancer concepts from clinical notes using natural language processing: a systematic review - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC10613366/
AI-Powered Oncology: Healthcare NLP's Role in Cancer Research and Treatment, https://www.johnsnowlabs.com/ai-powered-oncology-healthcare-nlps-role-in-cancer-research-and-treatment/
Natural Language Processing of Primary Care Data ... - Diva-portal.org, https://www.diva-portal.org/smash/get/diva2:1895835/FULLTEXT01.pdf
Early Detection AI Solutions: Clinical Decision Support - Origent Data Sciences, https://www.origent.com/applications/early-detection/
A Step-by-Step Journey in Referral Management System from Consultation to Follow-Up, https://www.cabotsolutions.com/blog/a-step-by-step-journey-in-referral-management-system-from-consultation-to-follow-up
Improving Referral Workflows: A Key Driver for Improving Patient Experience and Collections - Vyne Medical, https://vynemedical.com/blog/improving-referral-workflows-a-key-driver-for-improving-patient-experience-and-collections/
The use of artificial intelligence for cancer therapeutic decision-making - PMC - NIH, https://pmc.ncbi.nlm.nih.gov/articles/PMC12530061/
Natural Language Processing can reduce workload, increase timeliness and improve quality of breast cancer care | BCCRC, https://bccrc.ca/dept/qrt/dept/mit/articles/natural-language-processing-can-reduce-workload-increase-timeliness-and-improve-quality
