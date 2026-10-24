# Importa a biblioteca Streamlit para construir a interface web
import streamlit as st
# Importa o pandas para manipulação e análise dos dados
import pandas as pd
# Importa o codificador LabelEncoder para transformar variáveis textuais em números
from sklearn.preprocessing import LabelEncoder
# Importa a Regressão Logística para treinar o modelo de classificação
from sklearn.linear_model import LogisticRegression
# Importa a função para dividir os dados em conjuntos de treino e teste
from sklearn.model_selection import train_test_split
# Importa a biblioteca Plotly Express para geração simplificada de gráficos de dispersão
import plotly.express as px
# Importa a biblioteca de objetos gráficos do Plotly para criar o indicador customizado
import plotly.graph_objects as go

# Configura o título principal que será exibido no topo do aplicativo
st.title('Previsão de Inadimplência de Clientes')

# Lê os dados completos da planilha Excel usando o caminho relativo
df = pd.read_excel('inadimplencia-clientes.xlsx')

# Adiciona um título de cabeçalho na barra lateral esquerda
st.sidebar.header('Filtros do Histórico')

# Extrai a lista de opções exclusivas para a coluna de Vínculo Empregatício
opcoes_vinculo = df['Vínculo Empregatício'].dropna().unique().tolist()
vinculos_selecionados = st.sidebar.multiselect('Vínculo Empregatício', opcoes_vinculo, default=opcoes_vinculo)

# Extrai a lista de opções exclusivas para a coluna de Escolaridade
opcoes_escolaridade = df['Escolaridade'].dropna().unique().tolist()
escolaridades_selecionadas = st.sidebar.multiselect('Escolaridade', opcoes_escolaridade, default=opcoes_escolaridade)

# Remove as linhas que possuem valores ausentes para limpar a base usada no treinamento
df_limpo = df.dropna()
df_transformado = df_limpo.copy()

# Mapeia a coluna textual 'Situação' para valores numéricos onde 'Inadimplente' passa a ser o alvo positivo (1)
if 'Situação' in df_transformado.columns:
    df_transformado['Situação'] = df_transformado['Situação'].map({'Adimplente': 0, 'Inadimplente': 1})
    coluna_alvo = 'Situação'
elif 'Inadimplente' in df_transformado.columns:
    coluna_alvo = 'Inadimplente'
else:
    coluna_alvo = df_transformado.columns[-1]

# Identifica todas as colunas que contêm dados do tipo texto remanescentes
colunas_categoricas = df_transformado.select_dtypes(include=['object']).columns
le = LabelEncoder()

for col in colunas_categoricas:
    df_transformado[col] = le.fit_transform(df_transformado[col])

# Define a variável dependente y e as independentes X
y = df_transformado[coluna_alvo]
X = df_transformado.drop(columns=[coluna_alvo])

# Divide a base de dados em 80% para treino e 20% para teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
modelo = LogisticRegression(max_iter=1000)
modelo.fit(X_train, y_train)

st.success('Modelo de Regressão Logística treinado com sucesso utilizando toda a base de dados!')

st.subheader('Insira os dados do cliente para previsão em tempo real:')
dados_usuario = {}
col_inputs = st.columns(2)

for i, col in enumerate(X.columns):
    with col_inputs[i % 2]:
        if df_limpo[col].dtype == 'float64':
            dados_usuario[col] = st.number_input(f'Valor para {col}', value=float(df_limpo[col].mean()))
        elif df_limpo[col].dtype == 'int64':
            dados_usuario[col] = st.number_input(f'Valor para {col}', value=int(df_limpo[col].mean()), step=1)
        else:
            opcoes_originais = df_limpo[col].unique().tolist()
            escolha_usuario = st.selectbox(f'Selecione {col}', opcoes_originais)
            le_temp = LabelEncoder().fit(df_limpo[col])
            dados_usuario[col] = le_temp.transform([escolha_usuario])[0]

df_entrada = pd.DataFrame([dados_usuario])
prob_inadimplencia = modelo.predict_proba(df_entrada)[0][1] * 100.0

st.subheader('Probabilidade de Inadimplência Simulada')

fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = prob_inadimplencia,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Probabilidade de Inadimplência (%)"},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "darkblue"},
        'steps': [
            {'range': [0, 30], 'color': "lightgreen"},
            {'range': [30, 70], 'color': "khaki"},
            {'range': [70, 100], 'color': "salmon"}
        ]
    }
))
fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
st.plotly_chart(fig_gauge, use_container_width=True)

# Aplica os filtros selecionados na barra lateral ao dataframe original
df_historico_filtrado = df_limpo[
    df_limpo['Vínculo Empregatício'].isin(vinculos_selecionados) &
    df_limpo['Escolaridade'].isin(escolaridades_selecionadas)
]

st.subheader('Análises Visuais do Histórico Filtrado')

if len(vinculos_selecionados) == 0 or len(escolaridades_selecionadas) == 0:
    st.warning('Por favor, selecione pelo menos uma opção nos filtros da barra lateral esquerda para exibir os gráficos.')
else:
    df_historico_filtrado = df_historico_filtrado.copy()
    
    if 'Inadimplente' in df_historico_filtrado.columns:
        df_historico_filtrado['Situação_Grafico'] = df_historico_filtrado['Inadimplente'].map({0: 'Adimplente', 1: 'Inadimplente'})
        coluna_cor = 'Situação_Grafico'
    else:
        coluna_cor = None

    # Seleciona apenas colunas numéricas de forma segura para os eixos
    colunas_numericas = df_historico_filtrado.select_dtypes(include=['number']).columns.tolist()
    
    col_x = 'Renda Mensal' if 'Renda Mensal' in colunas_numericas else (colunas_numericas[0] if len(colunas_numericas) > 0 else df_historico_filtrado.columns[0])
    col_y = 'Valor da Parcela' if 'Valor da Parcela' in colunas_numericas else (colunas_numericas[1] if len(colunas_numericas) > 1 else df_historico_filtrado.columns[1])

    fig_scatter = px.scatter(
        df_historico_filtrado,
        x=col_x,
        y=col_y,
        color=coluna_cor,
        color_discrete_map={'Adimplente': 'blue', 'Inadimplente': 'red'} if coluna_cor else None,
        title=f'{col_x} vs {col_y}',
        labels={col_x: f'{col_x} (R$)', col_y: f'{col_y} (R$)'}
    )

    val_x = dados_usuario.get(col_x, df_limpo[col_x].mean() if col_x in df_limpo and pd.api.types.is_numeric_dtype(df_limpo[col_x]) else 0)
    val_y = dados_usuario.get(col_y, df_limpo[col_y].mean() if col_y in df_limpo and pd.api.types.is_numeric_dtype(df_limpo[col_y]) else 0)

    fig_scatter.add_trace(go.Scatter(
        x=[val_x],
        y=[val_y],
        mode='markers',
        marker=dict(color='yellow', size=15, symbol='star', line=dict(color='black', width=1.5)),
        name='Cliente Simulado'
    ))

    fig_scatter.update_layout(legend_title_text='Legenda', margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Gráfico de barras por atrasos anteriores (se a coluna existir)
    col_atrasos = 'Atrasos Anteriores' if 'Atrasos Anteriores' in df_historico_filtrado.columns else None
    
    if col_atrasos and 'Inadimplente' in df_historico_filtrado.columns:
        df_atrasos = df_historico_filtrado.groupby(col_atrasos)['Inadimplente'].mean().reset_index()
        df_atrasos['Taxa de Inadimplência (%)'] = df_atrasos['Inadimplente'] * 100.0

        atrasos_simulados = int(dados_usuario.get(col_atrasos, 0))

        cores_barras = [
            '#FF8C00' if row[col_atrasos] == atrasos_simulados else '#1F77B4'
            for idx, row in df_atrasos.iterrows()
        ]

        fig_barras = go.Figure(go.Bar(
            x=df_atrasos[col_atrasos],
            y=df_atrasos['Taxa de Inadimplência (%)'],
            marker_color=cores_barras,
            text=df_atrasos['Taxa de Inadimplência (%)'].round(1).astype(str) + '%',
            textposition='auto'
        ))

        fig_barras.update_layout(
            title='Taxa de Inadimplência Real por Faixa de Atrasos Anteriores',
            xaxis_title='Quantidade de Atrasos Anteriores',
            yaxis_title='Taxa de Inadimplência (%)',
            xaxis=dict(type='category'),
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_barras, use_container_width=True)
