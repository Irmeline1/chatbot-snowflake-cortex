import streamlit as st
from snowflake.snowpark.context import get_active_session
import uuid
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="Assistant IA – Snowflake Cortex", page_icon="💬")
session = get_active_session()

st.markdown("""
    <h1 style='text-align:center; font-size:32px; margin-bottom:20px;'>
        Assistant IA – Snowflake Cortex
    </h1>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR : PARAMÈTRES + CONVERSATIONS
# ==========================================
st.sidebar.header("⚙️ Paramètres")

model = st.sidebar.selectbox(
    "Modèle Cortex",
    ["llama3-8b", "mistral-large2", "mistral-7b"],
    index=0
)

st.sidebar.info("Modèles compatibles avec un compte Trial")

# Charger les conversations existantes
try:
    df_conv = session.sql(
        """
        SELECT conversation_id,
               MIN(timestamp) AS first_ts
        FROM DB_LAB.CHAT_APP.CONVERSATION_LOG
        GROUP BY conversation_id
        ORDER BY first_ts DESC
        LIMIT 20
        """
    ).to_pandas()
    conv_ids = df_conv["CONVERSATION_ID"].tolist()
except Exception:
    conv_ids = []

selected_conv = st.sidebar.selectbox(
    "Recharger une conversation",
    ["Nouvelle conversation"] + conv_ids,
    index=0
)

if st.sidebar.button("🆕 Nouveau chat"):
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()

# ==========================================
# INITIALISATION SESSION
# ==========================================
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

conversation_id = st.session_state.conversation_id

# ==========================================
# RELOAD D’UNE CONVERSATION EXISTANTE
# ==========================================
if selected_conv != "Nouvelle conversation":
    conversation_id = selected_conv
    st.session_state.conversation_id = selected_conv

    try:
        df_msgs = session.sql(
            """
            SELECT role, content
            FROM DB_LAB.CHAT_APP.CONVERSATION_LOG
            WHERE conversation_id = ?
            ORDER BY timestamp
            """,
            params=[conversation_id],
        ).to_pandas()

        st.session_state.messages = [
            {"role": row["ROLE"], "content": row["CONTENT"]}
            for _, row in df_msgs.iterrows()
        ]
    except Exception:
        st.session_state.messages = []

# ==========================================
# MINI-RAG : RÉCUPÉRATION DES ENTRÉES KB_FAQ
# ==========================================
def get_rag_entries(user_message: str):
    """
    Recherche simple dans KB_FAQ :
    - LIKE sur la question
    - Retourne jusqu'à 3 entrées (question, answer, source)
    """
    try:
        df_kb = session.sql(
            """
            SELECT question, answer, source
            FROM DB_LAB.CHAT_APP.KB_FAQ
            WHERE LOWER(question) LIKE LOWER(CONCAT('%', ?, '%'))
            LIMIT 3
            """,
            params=[user_message],
        ).to_pandas()

        entries = []
        for _, row in df_kb.iterrows():
            entries.append(
                {
                    "question": row["QUESTION"],
                    "answer": row["ANSWER"],
                    "source": row["SOURCE"],
                }
            )
        return entries
    except Exception:
        return []

# ==========================================
# APPEL CORTEX — PARAMÉTRÉ
# ==========================================
def ask_cortex(model: str, prompt: str) -> str:
    df = session.sql(
        """
        SELECT snowflake.cortex.complete(?, ?) AS response
        """,
        params=[model, prompt],
    ).collect()
    return df[0]["RESPONSE"]

# ==========================================
# CONSTRUCTION DU PROMPT (AVEC CONTEXTE RAG)
# ==========================================
def build_prompt(user_message: str, rag_entries) -> str:
    system_instruction = (
        "Tu es un assistant francophone clair, précis et factuel. "
        "Tu donnes des réponses courtes (2 à 4 phrases). "
        "Si des connaissances internes sont fournies, utilise-les. "
        "Ne répète jamais la question. Ne t'excuse jamais."
    )

    history = st.session_state.messages[-6:]

    history_text = ""
    for msg in history:
        if msg["role"] == "user":
            history_text += f"Utilisateur : {msg['content']}\n"
        elif msg["role"] == "assistant":
            history_text += f"Assistant : {msg['content']}\n"

    rag_text = ""
    if rag_entries:
        rag_text = "Connaissances internes :\n"
        for e in rag_entries:
            rag_text += f"- {e['question']} → {e['answer']} (Source : {e['source']})\n"

    full_prompt = f"""
{system_instruction}

Historique :
{history_text}

{rag_text}

Question :
{user_message}

Réponse :
"""
    return full_prompt.strip()

# ==========================================
# AFFICHAGE HISTORIQUE
# ==========================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ==========================================
# INPUT UTILISATEUR
# ==========================================
user_input = st.chat_input("Écrivez votre message...")

if user_input:
    # Affichage user
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Sauvegarde user
    session.sql(
        """
        INSERT INTO DB_LAB.CHAT_APP.CONVERSATION_LOG
        (conversation_id, timestamp, role, content)
        VALUES (?, ?, ?, ?)
        """,
        params=[conversation_id, datetime.now(), "user", user_input],
    ).collect()

    # Récupération des entrées RAG
    rag_entries = get_rag_entries(user_input)

    # Prompt complet avec contexte
    prompt_complet = build_prompt(user_input, rag_entries)

    # Appel Cortex
    try:
        bot_response = ask_cortex(model, prompt_complet)
    except Exception as e:
        bot_response = f"⚠️ Erreur Cortex : {str(e)}"
        rag_entries = []

    # Affichage assistant + sources
    with st.chat_message("assistant"):
        st.write(bot_response)

        if rag_entries:
            st.markdown("### 📚 Sources internes")
            for e in rag_entries:
                st.markdown(f"- **{e['source']}**")

    st.session_state.messages.append({"role": "assistant", "content": bot_response})

    # Sauvegarde assistant
    session.sql(
        """
        INSERT INTO DB_LAB.CHAT_APP.CONVERSATION_LOG
        (conversation_id, timestamp, role, content)
        VALUES (?, ?, ?, ?)
        """,
        params=[conversation_id, datetime.now(), "assistant", bot_response],
    ).collect()
