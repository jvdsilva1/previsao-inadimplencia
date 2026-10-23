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

# Lê os dados completos da planilha Excel usando o caminho relativo solicitado pelo usuário
df = pd.read_excel('inadimplencia-clientes.xlsx')

# Adiciona um título de cabeçalho na barra lateral esquerda
st.sidebar.header('Filtros do Histórico')

# Extrai a lista de opções exclusivas para a coluna de Vínculo Empregatício
opcoes_vinculo = df['Vínculo Empregatício'].dropna().unique().tolist()
# Cria o componente multiselect na barra lateral de Vínculo Empregatício com todas as opções marcadas de início
vinculos_selecionados = st.sidebar.multiselect('Vínculo Empregatício', opcoes_vinculo, default=opcoes_vinculo)

# Extrai a lista de opções exclusivas para a coluna de Escolaridade
opcoes_escolaridade = df['Escolaridade'].dropna().unique().tolist()
# Cria o componente multiselect na barra lateral de Escolaridade com todas as opções marcadas de início
escolaridades_selecionadas = st.sidebar.multiselect('Escolaridade', opcoes_escolaridade, default=opcoes_escolaridade)

# Remove as linhas que possuem valores ausentes para limpar a base usada no treinamento
df_limpo = df.dropna()
# Cria uma cópia dos dados limpos para aplicar as conversões numéricas necessárias
df_transformado = df_limpo.copy()

# Identifica todas as colunas que contêm dados do tipo texto
colunas_categoricas = df_transformado.select_dtypes(include=['object']).columns
# Inicializa o transformador para converter textos das categorias em números sequenciais
le = LabelEncoder()

# Loop que percorre cada coluna categórica para codificá-la numericamente
for col in colunas_categoricas:
    # Executa a codificação substituindo os textos por números para que o modelo possa ler
    df_transformado[col] = le.fit_transform(df_transformado[col])

# Define a variável dependente y do nosso modelo
y = df_transformado['Inadimplente']
# Define as variáveis independentes X removendo apenas a variável alvo
X = df_transformado.drop(columns=['Inadimplente'])

# Divide a base de dados em 80% para treino e 20% para teste para avaliação interna
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# Instancia o objeto classificador da Regressão Logística
modelo = LogisticRegression(max_iter=1000)
# Executa o ajuste do algoritmo de regressão logística com toda a base de dados tratada
modelo.fit(X_train, y_train)

# Exibe uma mensagem informativa notificando que o modelo de predição está devidamente calibrado
st.success('Modelo de Regressão Logística treinado com sucesso utilizando toda a base de dados!')

# Exibe o título da seção onde o usuário entrará com as variáveis do cliente simulado
st.subheader('Insira os dados do cliente para previsão em tempo real:')

# Cria o dicionário para guardar as entradas fornecidas pelo usuário
dados_usuario = {}

# Define as colunas lado a lado na interface principal para melhor aproveitamento do espaço
col_inputs = st.columns(2)

# Loop para percorrer cada feature necessária no modelo e gerar o respectivo widget
for i, col in enumerate(X.columns):
    # Alterna a inserção do controle visual entre a primeira e a segunda coluna de layout
    with col_inputs[i % 2]:
        # Verifica se a feature original requer dados numéricos decimais
        if df_limpo[col].dtype == 'float64':
            # Gera um campo de entrada numérica contínua com a média original como padrão
            dados_usuario[col] = st.number_input(f'Valor para {col}', value=float(df_limpo[col].mean()))
        # Verifica se a feature original requer dados numéricos inteiros
        elif df_limpo[col].dtype == 'int64':
            # Gera um campo de entrada numérica inteira com a média inteira original como padrão
            dados_usuario[col] = st.number_input(f'Valor para {col}', value=int(df_limpo[col].mean()), step=1)
        # Caso seja uma coluna de texto, cria uma seleção de opções mapeada para seu código numérico
        else:
            # Obtém as strings de texto únicas que existem na coluna original
            opcoes_originais = df_limpo[col].unique().tolist()
            # Gera um seletor visual contendo todas as strings descritivas mapeadas
            escolha_usuario = st.selectbox(f'Selecione {col}', opcoes_originais)
            # Inicializa um codificador temporário para a categoria específica
            le_temp = LabelEncoder().fit(df_limpo[col])
            # Transforma a seleção atual da string do usuário no código numérico esperado pelo modelo
            dados_usuario[col] = le_temp.transform([escolha_usuario])[0]

# Cria uma linha de dados com as informações do cliente atual simulado pelo usuário
df_entrada = pd.DataFrame([dados_usuario])
# Calcula a probabilidade de inadimplência (classe 1) para o registro inserido no formulário dinâmico
prob_inadimplencia = modelo.predict_proba(df_entrada)[0][1] * 100.0

# Adiciona o subtítulo da seção de métricas de probabilidade simulada
st.subheader('Probabilidade de Inadimplência Simulada')

# Constrói o gráfico de indicador visual do tipo velocímetro para mostrar a porcentagem prevista
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
# Reduz as margens internas do gráfico para otimizar o espaço visual do painel
fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
# Exibe o velocímetro na tela do aplicativo de forma integrada
st.plotly_chart(fig_gauge, use_container_width=True)

# Aplica os filtros selecionados na barra lateral ao dataframe original do histórico de clientes
df_historico_filtrado = df_limpo[
    df_limpo['Vínculo Empregatício'].isin(vinculos_selecionados) &
    df_limpo['Escolaridade'].isin(escolaridades_selecionadas)
]

# Mostra a seção de análise dispersiva baseada nos escolhas de filtro feitas na esquerda
st.subheader('Análises Visuais do Histórico Filtrado')

# Condicional para verificar se o usuário removeu todas as opções de filtro da barra lateral
if len(vinculos_selecionados) == 0 or len(escolaridades_selecionadas) == 0:
    # Mostra um alerta amigável de erro avisando que os filtros estão completamente vazios
    st.warning('Por favor, selecione pelo menos uma opção nos filtros da barra lateral esquerda para exibir os gráficos.')
# Caso exista dados para plotar com base nos filtros selecionados
else:
    # Mapeia as cores para a situação real de inadimplência da planilha histórica
    mapa_cores = {0: 'blue', 1: 'red'}
    # Associa rótulos textuais legíveis para as classes categóricas binárias do histórico
    df_historico_filtrado = df_historico_filtrado.copy()
    df_historico_filtrado['Situação'] = df_historico_filtrado['Inadimplente'].map({0: 'Adimplente', 1: 'Inadimplente'})

    # Gera o gráfico de dispersão dinâmico relacionando a Renda Mensal com o Valor da Parcela
    fig_scatter = px.scatter(
        df_historico_filtrado,
        x='Renda Mensal',
        y='Valor da Parcela',
        color='Situação',
        color_discrete_map={'Adimplente': 'blue', 'Inadimplente': 'red'},
        title='Renda Mensal vs Valor da Parcela',
        labels={'Renda Mensal': 'Renda Mensal (R$)', 'Valor da Parcela': 'Valor da Parcela (R$)'}
    )

    # Adiciona a marcação da estrela amarela que indica visualmente o cliente simulado pelos inputs
    fig_scatter.add_trace(go.Scatter(
        x=[dados_usuario.get('Renda Mensal', df_limpo['Renda Mensal'].mean())],
        y=[dados_usuario.get('Valor da Parcela', df_limpo['Valor da Parcela'].mean())],
        mode='markers',
        marker=dict(color='yellow', size=15, symbol='star', line=dict(color='black', width=1.5)),
        name='Cliente Simulado'
    ))

    # Ajusta o posicionamento da legenda e margens para melhorar a estética do gráfico de dispersão
    fig_scatter.update_layout(legend_title_text='Legenda', margin=dict(l=20, r=20, t=50, b=20))
    # Desenha o gráfico de dispersão com o destaque na página principal
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Agrupa o histórico filtrado para calcular a média real de inadimplentes (taxa em %) por número de atrasos anteriores
    df_atrasos = df_historico_filtrado.groupby('Atrasos Anteriores')['Inadimplente'].mean().reset_index()
    # Multiplica a proporção por 100 para converter o valor em percentual legível
    df_atrasos['Taxa de Inadimplência (%)'] = df_atrasos['Inadimplente'] * 100.0

    # Recupera o valor de atrasos anteriores configurado para o cliente atual no painel
    atrasos_simulados = int(dados_usuario.get('Atrasos Anteriores', 0))

    # Cria uma lista de cores onde cada barra recebe azul escuro por padrão, exceto a faixa do simulado que recebe laranja
    cores_barras = [
        '#FF8C00' if row['Atrasos Anteriores'] == atrasos_simulados else '#1F77B4'
        for idx, row in df_atrasos.iterrows()
    ]

    # Constrói o gráfico de barras representando a taxa percentual de inadimplência por Atrasos Anteriores
    fig_barras = go.Figure(go.Bar(
        x=df_atrasos['Atrasos Anteriores'],
        y=df_atrasos['Taxa de Inadimplência (%)'],
        marker_color=cores_barras,
        text=df_atrasos['Taxa de Inadimplência (%)'].round(1).astype(str) + '%',
        textposition='auto'
    ))

    # Configura e adiciona título, rótulos de eixos e ajusta visualmente o gráfico de barras
    fig_barras.update_layout(
        title='Taxa de Inadimplência Real por Faixa de Atrasos Anteriores',
        xaxis_title='Quantidade de Atrasos Anteriores',
        yaxis_title='Taxa de Inadimplência (%)',
        xaxis=dict(type='category'),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    # Desenha o terceiro gráfico de barras interativo na interface
    st.plotly_chart(fig_barras, use_container_width=True)
