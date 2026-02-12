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

# 🏗️ Mise en place de l’environnement 

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

SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

