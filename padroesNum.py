import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import json
from io import BytesIO

# Configuração da Página
st.set_page_config(
    page_title="Analisador de Padrões Numéricos Pro",
    page_icon="🧠",
    layout="wide"
)

# Estilo Customizado
st.markdown("""
    <style>
    .main {
        background-color: #09090b;
        color: #f4f4f5;
    }
    .stButton>button {
        background-color: #10b981;
        color: white;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #059669;
        border: none;
    }
    .prediction-box {
        background-color: #18181b;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #27272a;
        font-family: monospace;
        font-size: 1.2rem;
        line-height: 1.6;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização da API do Gemini
api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        st.error("Erro: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-3.1-pro-preview')

model = init_gemini()

def analyze_data(data_source, is_pdf=False):
    prompt = """
    Analise a série histórica de sequências numéricas fornecida.
    
    Seu objetivo é:
    1. Extrair/Analisar as sequências.
    2. Reconhecer padrões dentro de cada sequência e entre elas.
    3. Fornecer estatísticas detalhadas (frequência, média de somas, paridade).
    4. Realizar uma análise de "Retorno de Dezenas do Concurso Anterior", comparando cada sequência com a anterior e fornecendo uma análise estatística a cada bloco de 3 sequências.
    5. Sugerir 10 novas sequências (cada uma contendo exatamente 15 números) que tenham maior probabilidade de ocorrer se os padrões identificados se mantiverem, considerando especificamente a última sequência do histórico como base para o cálculo de retorno.
    
    IMPORTANTE: Você DEVE verificar se as sequências sugeridas já foram sorteadas na série histórica fornecida. Se alguma sequência sugerida já existir no histórico, você deve substituí-la por uma nova sequência inédita. Repita este processo até que todas as 10 sugestões sejam 100% inéditas.
    
    Responda estritamente em formato JSON seguindo esta estrutura:
    {
      "summary": "Resumo executivo da análise estatística",
      "returnAnalysis": "Relatório detalhado sobre o retorno de dezenas e análise comparativa a cada 3 sequências",
      "patterns": [
        { "name": "Nome do Padrão", "description": "Explicação detalhada", "confidence": 0.95 }
      ],
      "statistics": {
        "frequency": { "número": contagem_inteira },
        "averageSum": 150.5,
        "evenOddRatio": "3:3"
      },
      "predictions": [
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        ... (total 10 sequências de 15 números inéditas)
      ]
    }
    """
    
    try:
        if is_pdf:
            # Para PDF, enviamos o arquivo diretamente (multimodal)
            response = model.generate_content(
                [{"mime_type": "application/pdf", "data": data_source}, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
        else:
            # Para Excel/Dataframe, enviamos como texto JSON
            full_prompt = f"{prompt}\n\nDados:\n{json.dumps(data_source)}"
            response = model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Erro na análise da IA: {str(e)}")
        return None

# UI Principal
st.title("🧠 Analisador de Padrões Numéricos Pro")
st.subheader("IA avançada para análise estatística de sequências (PDF ou Excel)")

uploaded_file = st.file_uploader("Carregar Documento PDF ou Excel", type=["pdf", "xlsx", "xls"])

if uploaded_file is not None:
    if st.button("Analisar Arquivo Agora"):
        with st.spinner("O Gemini 3.1 Pro está processando os dados e identificando padrões matemáticos complexos..."):
            
            analysis_result = None
            
            if uploaded_file.type == "application/pdf":
                pdf_data = uploaded_file.read()
                analysis_result = analyze_data(pdf_data, is_pdf=True)
            else:
                # Processamento Excel
                df = pd.read_excel(uploaded_file, header=None)
                # Limpeza básica: pegar apenas números
                sequences = []
                for _, row in df.iterrows():
                    seq = [int(x) for x in row if pd.notnull(x) and str(x).isdigit()]
                    if seq:
                        sequences.append(seq)
                analysis_result = analyze_data(sequences)

            if analysis_result:
                st.success("Análise concluída com sucesso!")
                
                # Layout do Dashboard
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### 📝 Análise Estatística")
                    st.write(analysis_result.get("summary", ""))
                    
                    st.markdown("### 📈 Análise de Retorno (Concurso Anterior)")
                    st.info(analysis_result.get("returnAnalysis", ""))
                
                with col2:
                    st.markdown("### 📊 Métricas")
                    st.metric("Média das Somas", f"{analysis_result['statistics']['averageSum']:.1f}")
                    st.metric("Paridade (P:Í)", analysis_result['statistics']['evenOddRatio'])
                    
                    st.markdown("### 🔍 Padrões")
                    for p in analysis_result.get("patterns", []):
                        with st.expander(f"{p['name']} ({int(p['confidence']*100)}%)"):
                            st.write(p['description'])

                # Gráfico de Frequência
                st.markdown("### 📊 Distribuição de Frequência")
                freq_data = analysis_result['statistics']['frequency']
                chart_df = pd.DataFrame({
                    'Número': [int(k) for k in freq_data.keys()],
                    'Contagem': list(freq_data.values())
                }).sort_values('Número')
                st.bar_chart(chart_df.set_index('Número'))

                # Sugestões
                st.markdown("### 🚀 Sugestões Inéditas (Alta Probabilidade)")
                st.caption("Sequências de 15 números que nunca foram sorteadas no histórico.")
                
                preds_text = ""
                for pred in analysis_result.get("predictions", []):
                    line = " ".join(map(str, pred))
                    preds_text += line + "\n"
                
                st.markdown(f'<div class="prediction-box">{preds_text.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                
                st.download_button(
                    label="Baixar Sugestões (TXT)",
                    data=preds_text,
                    file_name="sugestoes_ineditas.txt",
                    mime="text/plain"
                )

st.divider()
st.caption("© 2024 Analisador de Padrões Numéricos Pro. Powered by Gemini 3.1 Pro.")

