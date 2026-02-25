import streamlit as st
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu App do AI Studio", page_icon="✨")

# --- CHAVE DA API ---
# No Streamlit Cloud, você configurará isso em 'Secrets'
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Por favor, adicione a GOOGLE_API_KEY nos Secrets do Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- CONFIGURAÇÕES DO AI STUDIO (COLE AQUI) ---
generation_config = {
  "temperature": 1, # <--- Cole o valor do AI Studio
  "top_p": 0.95,    # <--- Cole o valor do AI Studio
  "top_k": 40,      # <--- Cole o valor do AI Studio
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# --- INSTRUÇÃO DE SISTEMA (COLE AQUI) ---
system_instruction = "Analise o documento PDF anexo que contém uma série histórica de sequências numéricas.
    
    Seu objetivo é:
    1. Extrair todas as sequências numéricas presentes no documento.
    2. Reconhecer padrões dentro de cada sequência (ex: progressões, somas, paridade).
    3. Reconhecer padrões entre as sequências (ex: recorrência, ciclos, correlações temporais).
    4. Fornecer estatísticas detalhadas.
    5. Realizar uma análise de "Retorno de Dezenas do Concurso Anterior", comparando cada sequência com a anterior e fornecendo uma análise estatística a cada bloco de 3 sequências.
    6. Sugerir 10 novas sequências (cada uma contendo exatamente 15 números) que tenham maior probabilidade de ocorrer se os padrões identificados se mantiverem, considerando especificamente a última sequência do histórico como base para o cálculo de retorno.
    
    IMPORTANTE: Você DEVE verificar se as sequências sugeridas já foram sorteadas na série histórica fornecida. Se alguma sequência sugerida já existir no histórico, você deve substituí-la por uma nova sequência inédita. Repita este processo até que todas as 10 sugestões sejam 100% inéditas em relação ao histórico.
    
    Responda estritamente em formato JSON seguindo esta estrutura:
    {
      "summary": "Resumo executivo da análise estatística",
      "returnAnalysis": "Relatório detalhado sobre o retorno de dezenas e análise comparativa a cada 3 sequências",
      "patterns": [
        { "name": "Nome do Padrão", "description": "Explicação detalhada", "confidence": 0.95 }
      ],
      "statistics": {
        "frequency": { "número": "contagem" },
        "averageSum": 150.5,
        "evenOddRatio": "3:3"
      },
      "predictions": [
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        ... (total 10 sequências de 15 números inéditas)
      ]
    }"

model = genai.GenerativeModel(
  model_name="gemini-3.1-pro-preview", # <--- Verifique se o nome do modelo está certo
  generation_config=generation_config,
  system_instruction=system_instruction,
)

# --- LÓGICA DO CHAT ---
st.title("Meu Assistente Personalizado")

# Inicializa o histórico se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Como posso ajudar?"):
    # Adiciona mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera a resposta usando o modelo
    with st.chat_message("assistant"):
        # Prepara o chat com o histórico
        chat_session = model.start_chat(
            history=[
                {"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]}
                for m in st.session_state.messages[:-1]
            ]
        )
        
        response = chat_session.send_message(prompt)
        full_response = response.text
        st.markdown(full_response)
    
    # Adiciona resposta da IA ao histórico
    st.session_state.messages.append({"role": "assistant", "content": full_response})
