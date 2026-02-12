#  Assistant IA – Snowflake Cortex  
Application de type ChatGPT déployée dans **Streamlit in Snowflake**, utilisant **Snowflake Cortex** comme moteur LLM, sans clé OpenAI, avec persistance et mini‑RAG.

---

#  Objectif du projet

L’objectif est de créer une application web conversationnelle permettant à un utilisateur d’interagir avec un modèle LLM directement depuis Snowflake, via :

- Streamlit in Snowflake  
- Snowflake Cortex  
- Sans clé API externe  
- Avec historique des conversations  
- Avec un mini‑RAG basé sur une table interne  

---

#  Architecture technique


---

#  Mise en place de l’environnement 

## 1. Création des objets Snowflake

```sql
CREATE WAREHOUSE IF NOT EXISTS WH_LAB
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

CREATE DATABASE IF NOT EXISTS DB_LAB;
CREATE SCHEMA IF NOT EXISTS DB_LAB.CHAT_APP;

USE WAREHOUSE WH_LAB;
USE DATABASE DB_LAB;
USE SCHEMA CHAT_APP;

-- 2. Activation Cortex
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

3. Création de l’application Streamlit
Depuis Snowflake UI :
Worksheets → Streamlit → Create Streamlit App

 Interface Chat (Partie B)
L’application contient :

Un titre

Une zone d’affichage des messages

Une zone de saisie (st.chat_input)

Une sidebar avec :

Sélecteur de modèle Cortex

Bouton “Nouveau chat”

Liste des conversations existantes
st.session_state.messages = [
    {"role": "user/assistant", "content": "..."}
]
Intégration Cortex (Partie C)
Construction du prompt
Le prompt inclut :

Une instruction système

L’historique (6 derniers messages)

Le contexte RAG (si trouvé)

La question utilisateur

Appel Cortex (SQL paramétré)
SELECT snowflake.cortex.complete(?, ?) AS response
Persistance (Partie D)
Table d’historique
CREATE TABLE IF NOT EXISTS DB_LAB.CHAT_APP.CONVERSATION_LOG (
    conversation_id STRING,
    timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    role STRING,
    content STRING
);
Bonus : Mini‑RAG
Table KB_FAQ
CREATE TABLE IF NOT EXISTS DB_LAB.CHAT_APP.KB_FAQ (
    question STRING,
    answer STRING,
    source STRING
);
Données métier
INSERT INTO DB_LAB.CHAT_APP.KB_FAQ (question, answer, source) VALUES
('Qu’est-ce que SAP MDG ?', 'SAP Master Data Governance est un module SAP permettant de gérer, valider et gouverner les données de référence.', 'SAP Documentation'),
('Qu’est-ce que SAP FI ?', 'Module de comptabilité financière de SAP.', 'SAP Help Portal'),
('Qu’est-ce qu’un MDM ?', 'Discipline visant à centraliser et gouverner les données de référence.', 'Gartner'),
('Qu’est-ce que Snowflake ?', 'Plateforme cloud de data warehousing.', 'Snowflake Documentation');

Arborescence du repository
📦 chatbot-snowflake-cortex
 ┣ 📜 streamlit_app.py
 ┣ 📜 README.md
 ┣ 📂 sql
 │   ┣ create_objects.sql
 │   ┣ create_conversation_log.sql
 │   ┣ create_kb_faq.sql
 │   ┣ insert_kb_faq.sql
 │   ┗ setup_cortex.sql

