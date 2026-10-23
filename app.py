# Condicional para verificar se o utilizador removeu todas as opções de filtro
    if len(vinculos_selecionados) == 0 or len(escolaridades_selecionadas) == 0:
        st.warning('Por favor, selecione pelo menos uma opção nos filtros da barra lateral esquerda para exibir os gráficos.')
    else:
        # Cria uma cópia do histórico filtrado
        df_historico_filtrado = df_historico_filtrado.copy()
        
        # Verifica se a coluna de alvo existe para mapear os rótulos de forma segura
        if 'Inadimplente' in df_historico_filtrado.columns:
            df_historico_filtrado['Situação'] = df_historico_filtrado['Inadimplente'].map({0: 'Adimplente', 1: 'Inadimplente'})
            coluna_cor = 'Situação'
        else:
            coluna_cor = None

        # Seleciona apenas colunas numéricas de forma segura para o gráfico de dispersão
        colunas_numericas = df_historico_filtrado.select_dtypes(include=['number']).columns.tolist()
        
        # Define col_x e col_y preferencialmente se existirem
        col_x = 'Renda Mensal' if 'Renda Mensal' in colunas_numericas else (colunas_numericas[0] if len(colunas_numericas) > 0 else df_historico_filtrado.columns[0])
        col_y = 'Valor da Parcela' if 'Valor da Parcela' in colunas_numericas else (colunas_numericas[1] if len(colunas_numericas) > 1 else df_historico_filtrado.columns[1])

        # Gera o gráfico de dispersão dinâmico
        fig_scatter = px.scatter(
            df_historico_filtrado,
            x=col_x,
            y=col_y,
            color=coluna_cor,
            color_discrete_map={'Adimplente': 'blue', 'Inadimplente': 'red'} if coluna_cor else None,
            title=f'{col_x} vs {col_y}',
            labels={col_x: f'{col_x} (R$)', col_y: f'{col_y} (R$)'}
        )

        # Adiciona a marcação da estrela amarela verificando se os dados são estritamente numéricos
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
